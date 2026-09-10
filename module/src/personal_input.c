/* SPDX-License-Identifier: MIT
 * Event-driven state only: no timers, sleeping, queues, or key buffering.
 */
#include "personal_input.h"
#include <string.h>

void pi_init(struct pi_state *s) {
    memset(s, 0, sizeof(*s));
    s->owner = -1;
}
static bool short_interval(int64_t end, int64_t start) {
    return end >= start && end - start <= PI_TAP_MS;
}
static unsigned magic_count(const struct pi_state *s) {
    unsigned count = 0;
    for (unsigned i = 0; i < PI_KEYS; ++i)
        count += s->keys[i].down && s->keys[i].magic;
    return count;
}
void pi_activity(struct pi_state *s, unsigned position) {
    for (unsigned i = 0; i < PI_KEYS; ++i)
        if (i != position && s->keys[i].down && s->keys[i].magic)
            s->keys[i].used = true;
}
static void discard_other_candidates(struct pi_state *s, unsigned position) {
    for (unsigned i = 0; i < PI_KEYS; ++i) {
        if (i != position) {
            s->keys[i].tap_ready = false;
            s->keys[i].eligible = false;
        }
    }
}
static void select_layer(struct pi_state *s, unsigned layer, unsigned locked, int owner) {
    s->active = layer;
    s->locked = locked;
    s->owner = owner;
    ++s->generation;
}
void pi_layer_press(struct pi_state *s, unsigned position, unsigned layer, int64_t now) {
    if (position >= PI_KEYS || (layer != 1 && layer != 2 && layer != 4)) return;
    struct pi_key *key = &s->keys[position];
    if (key->down) return;
    bool double_tap = key->tap_ready && key->layer == layer &&
                      short_interval(now, key->released_at);
    pi_activity(s, position);
    discard_other_candidates(s, position);
    key->down = true;
    key->magic = false;
    key->tap_ready = false;
    key->pressed_at = now;
    key->layer = layer;
    key->eligible = false;
    if (s->locked == layer) {
        select_layer(s, 0, 0, -1);
        key->generation = 0;
        return;
    }
    bool lock = double_tap || magic_count(s) > 0;
    select_layer(s, layer, lock ? layer : 0, (int)position);
    key->generation = s->generation;
    key->eligible = !lock;
}
void pi_layer_release(struct pi_state *s, unsigned position, int64_t now) {
    if (position >= PI_KEYS) return;
    struct pi_key *key = &s->keys[position];
    if (!key->down || key->magic) return;
    key->down = false;
    bool owns = s->owner == (int)position && key->generation == s->generation;
    if (owns && !s->locked) {
        select_layer(s, 0, 0, -1);
        key->tap_ready = key->eligible && short_interval(now, key->pressed_at);
        key->released_at = now;
    }
    key->eligible = false;
}
void pi_magic_press(struct pi_state *s, unsigned position, int64_t now) {
    if (position >= PI_KEYS || s->keys[position].down) return;
    pi_activity(s, position);
    discard_other_candidates(s, position);
    s->keys[position] = (struct pi_key){.down = true, .magic = true,
                                      .used = magic_count(s) > 0, .pressed_at = now};
    select_layer(s, PI_MAGIC, 0, -1);
}
bool pi_magic_release(struct pi_state *s, unsigned position, int64_t now) {
    if (position >= PI_KEYS) return false;
    struct pi_key *key = &s->keys[position];
    if (!key->down || !key->magic) return false;
    key->down = false;
    bool status = !key->used && short_interval(now, key->pressed_at);
    if (s->active == PI_MAGIC && magic_count(s) == 0)
        select_layer(s, 0, 0, -1);
    return status;
}
bool pi_shift(struct pi_state *s, unsigned position, unsigned side, bool pressed) {
    if (position >= PI_KEYS || side > 1) return false;
    if (pressed) {
        if (s->shifts[position]) return false;
        s->shifts[position] = side + 1;
        ++s->shift_count[side];
    } else {
        if (!s->shifts[position]) return false;
        --s->shift_count[s->shifts[position] - 1];
        s->shifts[position] = 0;
    }
    if (!s->shift_count[0] && !s->shift_count[1]) s->caps_latched = false;
    if (s->shift_count[0] && s->shift_count[1] && !s->caps_latched) {
        s->caps_latched = true;
        return true;
    }
    return false;
}
