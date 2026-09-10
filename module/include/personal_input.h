/* SPDX-License-Identifier: MIT */
#ifndef PERSONAL_INPUT_H
#define PERSONAL_INPUT_H
#include <stdbool.h>
#include <stdint.h>

#define PI_KEYS 80
#define PI_TAP_MS 200
#define PI_MAGIC 3

struct pi_key {
    bool down, magic, used, tap_ready, eligible;
    uint8_t layer;
    int64_t pressed_at, released_at;
    uint32_t generation;
};
struct pi_state {
    uint8_t active, locked;
    uint32_t generation;
    int owner; /* meaningful only while a momentary typing layer is held */
    struct pi_key keys[PI_KEYS];
    uint8_t shifts[PI_KEYS];
    unsigned shift_count[2];
    bool caps_latched;
};
void pi_init(struct pi_state *s);
void pi_activity(struct pi_state *s, unsigned position);
void pi_layer_press(struct pi_state *s, unsigned position, unsigned layer, int64_t now);
void pi_layer_release(struct pi_state *s, unsigned position, int64_t now);
void pi_magic_press(struct pi_state *s, unsigned position, int64_t now);
bool pi_magic_release(struct pi_state *s, unsigned position, int64_t now);
/* Return true once per dual-Shift chord. The adapter forwards Shift first. */
bool pi_shift(struct pi_state *s, unsigned position, unsigned side, bool pressed);
#endif
