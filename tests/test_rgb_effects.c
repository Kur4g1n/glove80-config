/* Compile the actual patched firmware functions against deterministic timer/LED stubs. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#define IS_ENABLED(x) 1
#define K_NO_WAIT 0
#define K_MSEC(x) (x)
#define CONFIG_ZMK_RGB_UNDERGLOW_EFF_START 4
#define DT_PROP_OR(node,prop,fallback) THEME_COUNT
#define DT_PROP(node,prop) THEME_COUNT
#include "rgb_effect_enum.inc"
static uint32_t palette_colors[401*THEME_COUNT];
static uint8_t locked_layer;
struct zmk_behavior_binding { unsigned param1,param2; };
struct zmk_behavior_binding_event { unsigned position; };

static struct { int current_effect,animation_step; bool on,layer_enabled; } state,saved;
static int underglow_tick,underglow_off_work;
static bool led_strip=true,timer_running;
static int renders,last_layer,saves;
static void k_timer_start(void *timer,int first,int period){timer_running=true;}
static void k_timer_stop(void *timer){timer_running=false;}
static void *zmk_workqueue_lowprio_work_q(void){return NULL;}
static void k_work_submit_to_queue(void *queue,void *work){}
static void zmk_rgb_set_ext_power(void){}
static int zmk_rgb_underglow_save_state(void){saves++;return 0;}
static int rgb_underglow_top_layer(void){return 3;}
static void zmk_rgb_underglow_set_layer(int layer,bool wake){renders++;last_layer=layer;timer_running=false;}
typedef int (*settings_read_cb)(void *,void *,size_t);
static bool settings_name_steq(const char *a,const char *b,const char **next){*next=NULL;return !strcmp(a,b);}
static int read_saved(void *ctx,void *out,size_t len){memcpy(out,&saved,len);return len;}
int zmk_rgb_underglow_transient_on(void);
int zmk_rgb_underglow_transient_off(void);
#include "rgb_effects.inc"
int main(void){
    state.current_effect=4;state.on=true;state.layer_enabled=true;timer_running=false;
    for(int round=0;round<3;round++){
        for(int step=0;step<UNDERGLOW_EFFECT_NUMBER;step++){
            int effect=(4+step+1)%UNDERGLOW_EFFECT_NUMBER;
            assert(zmk_rgb_underglow_cycle_effect(1)==0);
            assert(state.current_effect==effect);
            assert(state.layer_enabled==(effect>=4));
            assert(timer_running==(effect<4));
            assert(zmk_rgb_underglow_palette_index()==(effect>=4?effect-4:0));
        }
    }
    assert(renders==3*THEME_COUNT && last_layer==3);
    assert(zmk_rgb_underglow_cycle_effect(-1)==0 && state.current_effect==3 && timer_running);
    assert(zmk_rgb_underglow_select_effect(4)==0 && !timer_running);
    assert(zmk_rgb_underglow_off()==0 && !state.on && !state.layer_enabled);
    int before=renders;
    for(int i=0;i<UNDERGLOW_EFFECT_NUMBER;i++)assert(zmk_rgb_underglow_cycle_effect(1)==0);
    assert(!state.on && !state.layer_enabled && !timer_running && renders==before);
    assert(zmk_rgb_underglow_on()==0 && state.on && state.layer_enabled && renders==before+1);
    for(int effect=0;effect<UNDERGLOW_EFFECT_NUMBER;effect++){
        saved=state;saved.current_effect=effect;saved.on=true;saved.layer_enabled=false;
        timer_running=false;
        assert(rgb_settings_set("state",sizeof(state),read_saved,NULL)==0);
        assert(state.current_effect==effect && state.layer_enabled==(effect>=4));
        assert(timer_running==(effect<4));
    }
    int effect=state.current_effect;
    assert(zmk_rgb_underglow_select_effect(-1)==-EINVAL);
    assert(zmk_rgb_underglow_select_effect(UNDERGLOW_EFFECT_NUMBER)==-EINVAL);
    assert(state.current_effect==effect);
    for(unsigned i=0;i<401*THEME_COUNT;i++)palette_colors[i]=1000+i;
    for(int theme=0;theme<THEME_COUNT;theme++){
        assert(zmk_rgb_underglow_select_effect(4+theme)==0);
        struct zmk_behavior_binding b={.param1=68,.param2=2};
        struct zmk_behavior_binding_event e={0};
        locked_layer=0;assert(palette_color(&b,e)==1000+401*theme+68);
        locked_layer=2;assert(palette_color(&b,e)==1000+401*theme+400);
        b.param2=0;assert(palette_color(&b,e)==1000+401*theme+68);
        b.param1=400;assert(palette_color(&b,e)==0);
    }
    saved=state;saved.current_effect=255;saved.on=true;
    assert(rgb_settings_set("state",sizeof(state),read_saved,NULL)==0 && state.current_effect==4);
    led_strip=false;assert(zmk_rgb_underglow_select_effect(0)==-ENODEV);
    printf("RGB: %d chosen palettes, stock effects, lock colors, off/on and saved effects passed\n",THEME_COUNT);
}
