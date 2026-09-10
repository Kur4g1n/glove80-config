zephyr_library()
zephyr_library_include_directories(include ${APPLICATION_SOURCE_DIR}/include)
if(CONFIG_PERSONAL_GLOVE80)
  zephyr_library_sources(src/behavior_lock_color.c)
  # The peripheral forwards physical positions; only the central runs the keymap.
  zephyr_library_sources_ifdef(CONFIG_ZMK_SPLIT_ROLE_CENTRAL
    src/personal_input.c
    src/behavior_personal.c
  )
endif()
