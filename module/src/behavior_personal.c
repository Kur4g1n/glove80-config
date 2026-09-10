/* SPDX-License-Identifier: MIT */
#include <zephyr/device.h>
#include <drivers/behavior.h>
#include <zmk/behavior.h>
#include <zmk/keymap.h>
#include <zmk/event_manager.h>
#include <zmk/events/position_state_changed.h>
#include <zmk/events/keycode_state_changed.h>
#include <dt-bindings/zmk/keys.h>
#include <dt-bindings/zmk/rgb.h>
#include "personal_input.h"
#include "personal_rgb.h"

static struct pi_state state = {.owner = -1};
static bool caps_down;
static void apply_state(uint8_t old_active, uint8_t old_locked) {
    /* Complete activation in the originating key event, before any RGB work. */
    if (state.active != old_active) zmk_keymap_layer_to(state.active);
    if (state.locked != old_locked) personal_rgb_lock(state.locked);
}
static int layer_press(struct zmk_behavior_binding *b, struct zmk_behavior_binding_event e) {
    uint8_t active = state.active, locked = state.locked;
    pi_layer_press(&state, e.position, b->param1, e.timestamp);
    apply_state(active, locked);
    return ZMK_BEHAVIOR_OPAQUE;
}
static int layer_release(struct zmk_behavior_binding *b, struct zmk_behavior_binding_event e) {
    uint8_t active = state.active, locked = state.locked;
    pi_layer_release(&state, e.position, e.timestamp);
    apply_state(active, locked);
    return ZMK_BEHAVIOR_OPAQUE;
}
static int magic_press(struct zmk_behavior_binding *b, struct zmk_behavior_binding_event e) {
    uint8_t active = state.active, locked = state.locked;
    pi_magic_press(&state, e.position, e.timestamp);
    apply_state(active, locked);
    return ZMK_BEHAVIOR_OPAQUE;
}
static int magic_release(struct zmk_behavior_binding *b, struct zmk_behavior_binding_event e) {
    uint8_t active = state.active, locked = state.locked;
    bool status = pi_magic_release(&state, e.position, e.timestamp);
    apply_state(active, locked);
    if (status) {
        const struct zmk_behavior_binding rgb = {
            .behavior_dev = DEVICE_DT_NAME(DT_NODELABEL(rgb_ug)), .param1 = RGB_STATUS_CMD};
        zmk_behavior_invoke_binding(&rgb, e, true);
        zmk_behavior_invoke_binding(&rgb, e, false);
    }
    return ZMK_BEHAVIOR_OPAQUE;
}
static int shift_event(struct zmk_behavior_binding *b, struct zmk_behavior_binding_event e, bool down) {
    /* Same event and timestamp as &kp. Do this BEFORE chord bookkeeping. */
    int result = raise_zmk_keycode_state_changed_from_encoded(b->param1, down, e.timestamp);
    if (pi_shift(&state, e.position, b->param1 == RSHFT, down)) {
        caps_down = true;
        raise_zmk_keycode_state_changed_from_encoded(CAPS, true, e.timestamp);
    }
    if (caps_down && (!state.shift_count[0] || !state.shift_count[1])) {
        caps_down = false;
        raise_zmk_keycode_state_changed_from_encoded(CAPS, false, e.timestamp);
    }
    return result;
}
static int shift_press(struct zmk_behavior_binding *b, struct zmk_behavior_binding_event e) {
    return shift_event(b, e, true);
}
static int shift_release(struct zmk_behavior_binding *b, struct zmk_behavior_binding_event e) {
    return shift_event(b, e, false);
}
static int activity_listener(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *ev = as_zmk_position_state_changed(eh);
    if (ev && ev->state) pi_activity(&state, ev->position);
    return ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(personal_activity, activity_listener);
ZMK_SUBSCRIPTION(personal_activity, zmk_position_state_changed);

static const struct behavior_driver_api layer_api = {
    .binding_pressed = layer_press, .binding_released = layer_release};
static const struct behavior_driver_api magic_api = {
    .binding_pressed = magic_press, .binding_released = magic_release};
static const struct behavior_driver_api shift_api = {
    .binding_pressed = shift_press, .binding_released = shift_release};

BEHAVIOR_DT_DEFINE(DT_NODELABEL(il), NULL, NULL, NULL, NULL, POST_KERNEL,
                   CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &layer_api);
BEHAVIOR_DT_DEFINE(DT_NODELABEL(im), NULL, NULL, NULL, NULL, POST_KERNEL,
                   CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &magic_api);
BEHAVIOR_DT_DEFINE(DT_NODELABEL(ish), NULL, NULL, NULL, NULL, POST_KERNEL,
                   CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &shift_api);
