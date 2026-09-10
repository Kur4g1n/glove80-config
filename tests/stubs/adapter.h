#pragma once
#include <stdbool.h>
#include <stdint.h>
#define LSHFT 225
#define RSHFT 229
#define CAPS 57
#define RGB_STATUS_CMD 15
#define ZMK_BEHAVIOR_OPAQUE 0
#define ZMK_EV_EVENT_BUBBLE 0
#define CONFIG_KERNEL_INIT_PRIORITY_DEFAULT 0
#define DT_NODELABEL(x) x
#define DEVICE_DT_NAME(x) #x
#define BEHAVIOR_DT_DEFINE(...)
#define ZMK_LISTENER(...)
#define ZMK_SUBSCRIPTION(...)
struct zmk_behavior_binding { const char *behavior_dev; uint32_t param1,param2; };
struct zmk_behavior_binding_event { int layer; unsigned position; int64_t timestamp; };
struct behavior_driver_api {
 int (*binding_pressed)(struct zmk_behavior_binding *,struct zmk_behavior_binding_event);
 int (*binding_released)(struct zmk_behavior_binding *,struct zmk_behavior_binding_event);
};
struct zmk_position_state_changed { unsigned position; bool state; };
typedef struct zmk_position_state_changed zmk_event_t;
static inline const struct zmk_position_state_changed *as_zmk_position_state_changed(const zmk_event_t *e) {return e;}
int raise_zmk_keycode_state_changed_from_encoded(uint32_t,bool,int64_t);
int zmk_keymap_layer_to(unsigned);
int zmk_behavior_invoke_binding(const struct zmk_behavior_binding *,struct zmk_behavior_binding_event,bool);
