/* Compile the actual firmware adapter against a synchronous event recorder. */
#include <assert.h>
#include <stdio.h>
#include "adapter.h"
struct record { unsigned code; bool down; int64_t time; } records[64];
static unsigned count,active,rgb;
int raise_zmk_keycode_state_changed_from_encoded(uint32_t code,bool down,int64_t t) {
    assert(count<64);records[count++]=(struct record){code,down,t};return 0;
}
int zmk_keymap_layer_to(unsigned layer) {active=layer;return 0;}
void personal_rgb_lock(uint8_t layer) {rgb=layer;}
int zmk_behavior_invoke_binding(const struct zmk_behavior_binding *b,struct zmk_behavior_binding_event e,bool down) {return 0;}
#include "../module/src/behavior_personal.c"
static void shift(unsigned side,bool down,int64_t now){
    struct zmk_behavior_binding b={.param1=side?RSHFT:LSHFT};
    struct zmk_behavior_binding_event e={.position=side?57:52,.timestamp=now};
    shift_event(&b,e,down);
}
static void caps_hold(unsigned first,unsigned released_first){
    count=0;
    shift(first,true,1234);
    assert(count==1 && records[0].time==1234);
    shift(!first,true,98765); // No timing requirement between Shift presses.
    assert(count==3 && records[1].code==(!first?RSHFT:LSHFT));
    assert(records[2].code==CAPS && records[2].down && records[2].time==98765);
    assert(caps_down);
    // Other input remains immediate during the held Caps key.
    raise_zmk_keycode_state_changed_from_encoded(4,true,98766);
    assert(count==4 && records[3].time==98766 && caps_down);
    shift(released_first,false,100000);
    assert(count==6 && !records[4].down && records[4].time==100000);
    assert(records[5].code==CAPS && !records[5].down && records[5].time==100000);
    assert(!caps_down);
    shift(released_first,true,100001); // Same chord: both must release before rearming.
    assert(count==7 && !caps_down);
    shift(!released_first,false,100002);shift(released_first,false,100003);
    assert(count==9 && !caps_down);
    // A quick new chord also releases Caps immediately, without a minimum timer.
    shift(0,true,100004);shift(1,true,100005);
    assert(count==12 && records[11].code==CAPS && records[11].down);
    shift(0,false,100006);
    assert(count==14 && records[13].code==CAPS && !records[13].down && records[13].time==100006);
    shift(1,false,100007);assert(count==15 && !caps_down);
}
int main(void) {
    for(unsigned first=0;first<2;first++)
        for(unsigned released_first=0;released_first<2;released_first++)
            caps_hold(first,released_first);
    struct zmk_behavior_binding num={.param1=2};
    struct zmk_behavior_binding_event e={.position=67,.timestamp=200000};
    layer_press(&num,e);assert(active==2 && rgb==0);
    e.timestamp+=30;layer_release(&num,e);assert(active==0);
    e.timestamp+=30;layer_press(&num,e);assert(active==2 && rgb==2);
    e.timestamp+=30;layer_release(&num,e);assert(active==2 && rgb==2);
    puts("Firmware adapter: immediate Shift, Caps held until either Shift releases, both orders and rearming passed");
}
