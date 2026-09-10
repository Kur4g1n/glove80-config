// Validate with the native loader without changing the selected input source.
// Successful registration here does not prove Settings refreshed its session cache.
import Foundation
import Carbon

func fail(_ message: String) -> Never {
    fputs(message + "\n", stderr)
    exit(1)
}

guard CommandLine.arguments.count == 2 else { fail("Usage: register-macos.swift BUNDLE") }
let location = URL(fileURLWithPath: CommandLine.arguments[1])
let status = TISRegisterInputSource(location as CFURL)
guard status == noErr else { fail("macOS registration failed (\(status)).") }

func property(_ source: TISInputSource, _ key: CFString) -> AnyObject? {
    guard let pointer = TISGetInputSourceProperty(source, key) else { return nil }
    return Unmanaged<AnyObject>.fromOpaque(pointer).takeUnretainedValue()
}

let sources = TISCreateInputSourceList(nil, true).takeRetainedValue() as! [TISInputSource]
// Resolve bundle metadata before comparing IDs; HIToolbox initially exposes
// synthesized IDs until the localized name has been requested.
for source in sources { _ = property(source, kTISPropertyLocalizedName) }
for (name, firstLetter) in [("English", "a"), ("RussianPC", "ф")] {
    let id = "org.glove80.inputmethod." + name
    guard let source = sources.first(where: { property($0, kTISPropertyInputSourceID) as? String == id }),
          let data = property(source, kTISPropertyUnicodeKeyLayoutData) as? Data else {
        fail("macOS did not load Glove80 \(name). Registration alone was insufficient.")
    }
    // Exercise native translation too: laptop A stays native; Option+A is ASCII.
    for (modifiers, expected) in [(UInt32(0), firstLetter), (UInt32(optionKey >> 8), "a")] {
        var deadKey: UInt32 = 0
        var length = 0
        var output = [UniChar](repeating: 0, count: 4)
        let result = data.withUnsafeBytes { bytes in
            UCKeyTranslate(bytes.baseAddress!.assumingMemoryBound(to: UCKeyboardLayout.self),
                           0, UInt16(kUCKeyActionDown), modifiers, UInt32(LMGetKbdType()),
                           OptionBits(kUCKeyTranslateNoDeadKeysMask), &deadKey,
                           output.count, &length, &output)
        }
        guard result == noErr, String(utf16CodeUnits: output, count: length) == expected else {
            fail("Glove80 \(name) failed native key translation (modifiers \(modifiers)).")
        }
    }
    print("Native layout translation verified: Glove80 \(name)")
}
