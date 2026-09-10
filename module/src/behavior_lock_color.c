/* SPDX-License-Identifier: MIT */
#include <zephyr/device.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <drivers/behavior.h>
#include <zmk/behavior.h>
#include <zmk/keymap.h>
#include <zmk/rgb_underglow.h>
#include <dt-bindings/zmk/rgb.h>
#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
#include <zmk/split/central.h>
#endif
#include <zmk/event_manager.h>
#include <zmk/events/underglow_color_changed.h>
#include "personal_rgb.h"

static uint8_t locked_layer;
static atomic_t requested_lock;
static atomic_t reconnect_effect;
static int set_lock(struct zmk_behavior_binding *b, struct zmk_behavior_binding_event e) {
    locked_layer = b->param1;
    raise_zmk_underglow_color_changed((struct zmk_underglow_color_changed){
        .layers = 0x1f, .wakeup = true});
    return ZMK_BEHAVIOR_OPAQUE;
}
static int lock_color(struct zmk_behavior_binding *b, struct zmk_behavior_binding_event e) {
    return locked_layer && locked_layer == b->param1 ? DT_PROP(DT_NODELABEL(lkcolor), locked_color) : (int)b->param2;
}
static const struct behavior_driver_api state_api = {
    .binding_pressed = set_lock, .locality = BEHAVIOR_LOCALITY_GLOBAL};
static const struct behavior_driver_api color_api = {
    .binding_pressed = lock_color, .locality = BEHAVIOR_LOCALITY_GLOBAL};
BEHAVIOR_DT_DEFINE(DT_NODELABEL(lkset), NULL, NULL, NULL, NULL, POST_KERNEL,
                   CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &state_api);
BEHAVIOR_DT_DEFINE(DT_NODELABEL(lkcolor), NULL, NULL, NULL, NULL, POST_KERNEL,
                   CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &color_api);

/* LED updates and split transport never sit in the input activation path. */
static void sync_lock(struct k_work *work) {
#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    if (atomic_cas(&reconnect_effect, 1, 0)) {
        /* Catch up a half that missed palette changes while disconnected. */
        bool on;
        zmk_rgb_underglow_get_state(&on);
        struct zmk_behavior_binding rgb = {
            .behavior_dev = DEVICE_DT_NAME(DT_NODELABEL(rgb_ug)),
            .param1 = RGB_EFS_CMD, .param2 = zmk_rgb_underglow_calc_effect(0)};
        const struct zmk_behavior_binding_event event = {.timestamp = k_uptime_get()};
        zmk_behavior_invoke_binding(&rgb, event, true);
        rgb.param1 = on ? RGB_ON_CMD : RGB_OFF_CMD;
        rgb.param2 = 0;
        zmk_behavior_invoke_binding(&rgb, event, true);
    }
    zmk_split_central_update_layers(zmk_keymap_layer_state());
#endif
    const struct zmk_behavior_binding b = {
        .behavior_dev = DEVICE_DT_NAME(DT_NODELABEL(lkset)), .param1 = atomic_get(&requested_lock)};
    const struct zmk_behavior_binding_event e = {.timestamp = k_uptime_get()};
    zmk_behavior_invoke_binding(&b, e, true);
}
K_WORK_DEFINE(lock_work, sync_lock);
void personal_rgb_lock(uint8_t layer) {
    atomic_set(&requested_lock, layer);
    k_work_submit(&lock_work);
}

void personal_rgb_connected(void) {
    atomic_set(&reconnect_effect, 1);
    k_work_submit(&lock_work);
}

#if DT_NODE_HAS_STATUS(DT_NODELABEL(palette_rgb), okay)
/* The stock RGB effect command is sent as an absolute effect to both halves. */
extern uint8_t zmk_rgb_underglow_palette_index(void);
static const uint32_t palette_colors[] = DT_PROP(DT_NODELABEL(palette_rgb), colors);
BUILD_ASSERT(ARRAY_SIZE(palette_colors) == DT_PROP(DT_NODELABEL(palette_rgb), theme_count) * 401);
static int palette_color(struct zmk_behavior_binding *b, struct zmk_behavior_binding_event e) {
    unsigned theme = zmk_rgb_underglow_palette_index();
    if (theme >= DT_PROP(DT_NODELABEL(palette_rgb), theme_count) || b->param1 >= 400) return 0;
    unsigned index = locked_layer && locked_layer == b->param2 ? 400 : b->param1;
    return palette_colors[theme * 401 + index];
}
static const struct behavior_driver_api palette_api = {
    .binding_pressed = palette_color, .locality = BEHAVIOR_LOCALITY_GLOBAL};
BEHAVIOR_DT_DEFINE(DT_NODELABEL(palette_rgb), NULL, NULL, NULL, NULL, POST_KERNEL,
                   CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &palette_api);
#endif
