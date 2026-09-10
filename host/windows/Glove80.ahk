#Requires AutoHotkey v2.0
#SingleInstance Force
#Include Lib\AutoHotInterception.ahk

; Run from AutoHotInterception's AHK v2 directory with layout.tsv and settings.ini.
; Stock English/Russian input sources stay selected. Only Glove80 is transformed.
Persistent
SetWorkingDir(A_ScriptDir)
if !FileExist("settings.ini") {
    MsgBox("Copy settings.ini.example to settings.ini and enter Glove80's VID/PID or exact Handle from Monitor.ahk.")
    ExitApp
}
VID := Integer(IniRead("settings.ini", "Glove80", "VID", "0"))
PID := Integer(IniRead("settings.ini", "Glove80", "PID", "0"))
DeviceHandle := IniRead("settings.ini", "Glove80", "Handle", "")
if DeviceHandle = "" && (!VID || !PID) {
    MsgBox("Set Glove80's nonzero VID/PID or exact Handle in settings.ini. No keyboard has been intercepted.")
    ExitApp
}
SwapThumbs := Integer(IniRead("settings.ini", "Glove80", "SwapThumbs", "1"))
AHI := AutoHotInterception()
Layout := Map()
for line in StrSplit(FileRead("layout.tsv", "UTF-8"), "`n", "`r") {
    if !line || SubStr(line, 1, 1) = ";"
        continue
    fields := StrSplit(line, "`t")
    values := []
    loop 6
        values.Push(Integer(fields[A_Index + 1]))
    Layout[Integer(fields[1])] := values
}
Device := 0
Physical := Map()
Pressed := Map()
OnExit(Stop)
; Re-identify on reconnect: Interception IDs can change after unplugging.
SetTimer(Connect, 1000)
Connect()

Connect() {
    global Device
    ; The wrapper's GetKeyboardId exits the app when absent; the underlying
    ; lookup returns zero, so the helper can wait for a disconnected keyboard.
    found := DeviceHandle != "" ? AHI.Instance.GetDeviceIdFromHandle(false, DeviceHandle, 1) : AHI.Instance.GetDeviceId(false, VID, PID, 1)
    if found = Device
        return
    Stop()
    if found {
        Device := found
        AHI.SubscribeKeyboard(Device, true, KeyEvent)
    }
}

Stop(*) {
    global Device
    if Device {
        for scan, output in Pressed {
            if output
                AHI.SendKeyEvent(Device, output, 0)
        }
        AHI.UnsubscribeKeyboard(Device)
    }
    Device := 0
    Pressed.Clear()
    Physical.Clear()
}

Held(scan) => Physical.Has(scan)

Russian() {
    ; Modern editors can host text input on a different thread from the frame.
    hwnd := DllCall("GetForegroundWindow", "Ptr")
    info := Buffer(8 + 6 * A_PtrSize + 16, 0)
    NumPut("UInt", info.Size, info)
    if DllCall("GetGUIThreadInfo", "UInt", 0, "Ptr", info) {
        focus := NumGet(info, 8 + A_PtrSize, "Ptr")
        if focus
            hwnd := focus
    }
    threadId := DllCall("GetWindowThreadProcessId", "Ptr", hwnd, "Ptr", 0, "UInt")
    return (DllCall("GetKeyboardLayout", "UInt", threadId, "UPtr") & 0xFFFF) = 0x0419
}

UnicodeKey(codepoint) {
    ; One complete down/up pair. No clipboard, layout switching, or delayed timer.
    size := A_PtrSize = 8 ? 40 : 28
    offset := A_PtrSize = 8 ? 8 : 4
    input := Buffer(size * 2, 0)
    loop 2 {
        base := (A_Index - 1) * size
        NumPut("UInt", 1, input, base)
        NumPut("UShort", codepoint, input, base + offset + 2)
        NumPut("UInt", A_Index = 1 ? 4 : 6, input, base + offset + 4)
    }
    DllCall("SendInput", "UInt", 2, "Ptr", input, "Int", size)
}

KeyEvent(scan, state) {
    global Physical, Pressed
    if !state {
        if Physical.Has(scan)
            Physical.Delete(scan)
        if Pressed.Has(scan) {
            output := Pressed[scan]
            Pressed.Delete(scan)
            if output
                AHI.SendKeyEvent(Device, output, 0)
        }
        return
    }
    Physical[scan] := true
    ; The firmware reserves right Alt as the Number/Symbol output-bank marker.
    if scan = 0x138 {
        Pressed[scan] := 0
        return
    }
    ; Keep a raw press's release paired even if language/modifiers change mid-hold.
    if Pressed.Has(scan) && Pressed[scan] {
        AHI.SendKeyEvent(Device, Pressed[scan], 1)
        return
    }
    output := scan
    if SwapThumbs {
        if scan = 0x15B
            output := 0x1D
        else if scan = 0x1D
            output := 0x15B
        else if scan = 0x15C
            output := 0x11D
    }
    shortcut := Held(0x1D) || Held(0x11D) || Held(0x15B) || Held(0x15C) || Held(0x38)
    if Layout.Has(scan) && !shortcut {
        isRussian := Russian()
        values := Layout[scan]
        ; Firmware already emits US scan codes. Keep real down/up events in
        ; English so games can read held keys; the right-Alt bank marker is
        ; still consumed above. Russian mapping continues to use Unicode.
        if !isRussian && values[1] {
            Pressed[scan] := output
            AHI.SendKeyEvent(Device, output, 1)
            return
        }
        pair := Held(0x138) ? 5 : isRussian ? 3 : 1
        lower := values[pair]
        shifted := Held(0x2A) || Held(0x36)
        if lower && RegExMatch(Chr(lower), "^[A-Za-zА-Яа-яЁё]$") && GetKeyState("CapsLock", "T")
            shifted := !shifted
        char := values[pair + (shifted ? 1 : 0)]
        Pressed[scan] := 0
        if char
            UnicodeKey(char)
        return
    }
    ; Extra Russian letter signals must never become F-key shortcuts in English.
    if scan >= 100 && scan <= 102 {
        Pressed[scan] := 0
        return
    }
    Pressed[scan] := output
    AHI.SendKeyEvent(Device, output, 1)
}
