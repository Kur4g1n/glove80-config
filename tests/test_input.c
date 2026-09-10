/* SPDX-License-Identifier: MIT */
#include "personal_input.h"
#include <assert.h>
#include <stdio.h>

static struct pi_state s;
static void expect(int active, int locked) { assert(s.active==active); assert(s.locked==locked); }
static void lock(unsigned key,unsigned layer,int64_t t) {
    pi_layer_press(&s,key,layer,t); expect(layer,0);
    pi_layer_release(&s,key,t+30); expect(0,0);
    pi_layer_press(&s,key,layer,t+70); expect(layer,layer);
    pi_layer_release(&s,key,t+100); expect(layer,layer);
}
static void holds_and_taps(void) {
    unsigned positions[]={68,67,75},layers[]={1,2,4};
    for(unsigned i=0;i<3;i++) {
        pi_init(&s);
        pi_layer_press(&s,positions[i],layers[i],0); expect(layers[i],0);
        pi_layer_release(&s,positions[i],500); expect(0,0);
        /* A long hold is not the first half of a double tap. */
        pi_layer_press(&s,positions[i],layers[i],520); expect(layers[i],0);
        pi_layer_release(&s,positions[i],550); expect(0,0);
        pi_layer_press(&s,positions[i],layers[i],751); expect(layers[i],0);
        pi_layer_release(&s,positions[i],1050); expect(0,0);
        lock(positions[i],layers[i],1200);
        pi_layer_press(&s,positions[i],layers[i],1400); expect(0,0);
        pi_layer_release(&s,positions[i],1430); expect(0,0);
        pi_layer_press(&s,positions[i],layers[i],1450); expect(layers[i],0);
    }
    pi_init(&s);
    pi_layer_press(&s,68,1,100);pi_layer_release(&s,68,300);
    pi_layer_press(&s,68,1,500);expect(1,1); /* inclusive boundaries */
    pi_init(&s);
    pi_layer_press(&s,68,1,300);pi_layer_release(&s,68,330);
    pi_layer_press(&s,68,1,200);expect(1,0); /* reordered/invalid timestamp */
    pi_init(&s);
    pi_layer_press(&s,68,1,0);pi_layer_release(&s,68,10);
    pi_activity(&s,24); /* letters neither wait nor take part in timing */
    pi_layer_press(&s,68,1,100);expect(1,1);
}
static void switches(void) {
    unsigned positions[]={68,67,75},layers[]={1,2,4};
    for(unsigned a=0;a<3;a++)for(unsigned b=0;b<3;b++)if(a!=b) {
        for(int order=0;order<2;order++) {
            pi_init(&s);
            pi_layer_press(&s,positions[a],layers[a],0);
            pi_layer_press(&s,positions[b],layers[b],20);expect(layers[b],0);
            if(order==0) {
                pi_layer_release(&s,positions[a],40);expect(layers[b],0);
                pi_layer_release(&s,positions[b],500);expect(0,0);
            } else {
                pi_layer_release(&s,positions[b],500);expect(0,0);
                pi_layer_release(&s,positions[a],520);expect(0,0);
            }
            pi_layer_press(&s,positions[a],layers[a],550);expect(layers[a],0);
        }
        pi_init(&s);lock(positions[a],layers[a],0);
        pi_layer_press(&s,positions[b],layers[b],150);expect(layers[b],0);
        pi_layer_release(&s,positions[b],500);expect(0,0);
    }
    /* A superseded key cannot undo a newer lock. */
    pi_init(&s);pi_layer_press(&s,68,1,0);
    pi_magic_press(&s,64,10);pi_layer_press(&s,75,4,20);expect(4,4);
    pi_layer_release(&s,68,25);expect(4,4);
    pi_layer_release(&s,75,30);assert(!pi_magic_release(&s,64,40));expect(4,4);
}
static void magic(void) {
    for(unsigned magic=64;magic<=79;magic+=15)for(int order=0;order<2;order++) {
        pi_init(&s);pi_magic_press(&s,magic,0);expect(3,0);
        pi_layer_press(&s,75,4,20);expect(4,4);
        if(order) {
            assert(!pi_magic_release(&s,magic,40));expect(4,4);
            pi_layer_release(&s,75,50);expect(4,4);
        } else {
            pi_layer_release(&s,75,40);expect(4,4);
            assert(!pi_magic_release(&s,magic,50));expect(4,4);
        }
        pi_magic_press(&s,magic,200);expect(3,0);
        assert(!pi_magic_release(&s,magic,500));expect(0,0);
    }
    pi_init(&s);pi_magic_press(&s,64,0);assert(pi_magic_release(&s,64,50));expect(0,0);
    pi_magic_press(&s,64,100);pi_activity(&s,23);
    assert(!pi_magic_release(&s,64,120));expect(0,0);
    pi_magic_press(&s,64,200);pi_magic_press(&s,79,220);
    assert(!pi_magic_release(&s,64,230));expect(3,0);
    assert(!pi_magic_release(&s,79,250));expect(0,0);
    pi_magic_press(&s,64,260);pi_magic_press(&s,79,270);
    assert(!pi_magic_release(&s,79,280));expect(3,0);
    assert(!pi_magic_release(&s,64,290));expect(0,0);
    /* Second press of either Magic key never locks Magic. */
    pi_magic_press(&s,64,300);pi_magic_release(&s,64,320);
    pi_magic_press(&s,64,340);expect(3,0);pi_magic_release(&s,64,360);expect(0,0);
}
static void shifts(void) {
    for(int reverse=0;reverse<2;reverse++) {
        unsigned p=reverse?57:52,q=reverse?52:57;
        pi_init(&s);
        assert(!pi_shift(&s,p,reverse,true));
        assert(pi_shift(&s,q,!reverse,true));
        assert(!pi_shift(&s,q,!reverse,true)); /* duplicate press */
        assert(!pi_shift(&s,q,!reverse,false));
        assert(!pi_shift(&s,q,!reverse,true)); /* both must release to rearm */
        assert(!pi_shift(&s,p,reverse,false));
        assert(!pi_shift(&s,q,!reverse,false));
        assert(!pi_shift(&s,p,reverse,true));
        assert(pi_shift(&s,q,!reverse,true));
    }
    pi_init(&s);
    assert(!pi_shift(&s,52,0,false));
    assert(!pi_shift(&s,52,0,true));assert(!pi_shift(&s,22,0,true));
    assert(!pi_shift(&s,52,0,false));assert(pi_shift(&s,57,1,true));
    assert(!pi_shift(&s,80,0,true));assert(!pi_shift(&s,20,2,true));
}
int main(void) {
    holds_and_taps();switches();magic();shifts();
    puts("Input sequences: immediate holds, tap boundaries, locks, overlaps, Magic, dual Shift passed");
}
