# Monika's ???? Event
# deserves it's own file because of how much dialogue these have
# it basically shows a new screen over everything, and has an image map
# Monika reacts to he place the player clicks


# Start lvl to start calculations from
# NOTE: being set to an int when the user unlocks the islands
default persistent._mas_islands_start_lvl = None
# Current progress, -1 means not unlocked yet
default persistent._mas_islands_progress = store.mas_island_event.DEF_PROGRESS
# Most of the progression is linear, but some things are unlocked at random
# that's so every player gets a bit different progression.
# Bear in mind, if you decide to add a new item, you'll need an update script
default persistent._mas_islands_unlocks = store.mas_island_event.IslandsDataDefinition.getDefaultUnlocks()

# Will be loaded later
init python in audio:
    # can't use define with mutable data
    # default just doesn't work /shrug
    isld_isly_clear = None
    isld_isly_rain = None
    isld_isly_snow = None


### initialize the island images
init 1:
    #   if for some reason we fail to convert the files into images
    #   then we must backout of showing the event.
    #
    #   NOTE: other things to note:
    #       on o31, we cannot have islands event
    define mas_decoded_islands = store.mas_island_event.decode_data()
    define mas_cannot_decode_islands = not mas_decoded_islands

    python:
        def mas_canShowIslands(flt=None):
            """
            Global check for whether or not we can show the islands event
            This only checks the technical side, NOT event unlocks

            IN:
                flt - the filter to use in check
                    If None, we fetch the current filter
                    If False, we don't check the fitler at all
                    (Default: None)

            OUT:
                boolean
            """
            # If None, get the current flt
            if flt is None:
                flt = mas_sprites.get_filter()

            # IF False, we don't need to check the flt
            elif flt is False:
                return mas_decoded_islands

            return mas_decoded_islands and mas_island_event.isFilterSupported(flt)


# A bunch of transforms we use for the final islands event
transform mas_islands_final_reveal_trans_1(delay, move_time):
    zoom 3.2
    align (0.45, 0.0)

    pause delay
    linear move_time align (0.9, 0.0)

transform mas_islands_final_reveal_trans_2(delay, move_time):
    zoom 2.5
    align (0.15, 0.5)

    pause delay
    linear move_time align (0.0, 0.2) zoom 1.9

transform mas_islands_final_reveal_trans_3(delay, move_time, zoom_time):
    zoom 3.0
    align (1.0, 0.2)

    pause delay
    linear move_time align (0.7, 0.6)
    linear zoom_time zoom 1.0

transform mas_islands_final_reveal_trans_4(delay, zoom_time):
    align (0.62, 0.55)
    pause delay
    linear zoom_time zoom 10.0


# Transform for weather overlays
transform mas_islands_weather_overlay_transform(speed=1.0, img_width=1500, img_height=2000):
    animation

    subpixel True
    anchor (0.0, 0.0)

    block:
        crop (img_width-config.screen_width, img_height-config.screen_height, 1280, 720)
        linear speed crop (0, 0, config.screen_width, config.screen_height)
        repeat

# Overlay image for the lightning effect
image mas_islands_lightning_overlay:
    animation

    alpha 0.75

    block:
        # Set the def child
        mas_island_event.NULL_DISP

        # Select wait time
        block:
            choice 0.3:
                pause 5.0
            choice 0.4:
                pause 10.0
            choice 0.3:
                pause 15.0

        # Choice showing lightning or skip
        block:
            choice (1.0 / mas_globals.lightning_chance):
                "mas_lightning"
                pause 0.1
                function mas_island_event._play_thunder
                pause 3.0
            choice (1.0 - 1.0/mas_globals.lightning_chance):
                pass

        repeat


# ## Base room
# # Day images
# image living_room_day = mas_island_event._get_room_sprite("d", False)
# image living_room_day_rain = mas_island_event._get_room_sprite("d_r", False)
# image living_room_day_overcast = "living_room_day_rain"
# image living_room_day_snow = mas_island_event._get_room_sprite("d_s", False)
# # Night images
# image living_room_night = mas_island_event._get_room_sprite("n", False)
# image living_room_night_rain = mas_island_event._get_room_sprite("n_r", False)
# image living_room_night_overcast = "living_room_night_rain"
# image living_room_night_snow = mas_island_event._get_room_sprite("n_s", False)
# # Sunset images
# image living_room_ss = mas_island_event._apply_flt_on_room_sprite("living_room_day", mas_sprites.FLT_SUNSET)
# image living_room_ss_rain = mas_island_event._apply_flt_on_room_sprite("living_room_day_rain", mas_sprites.FLT_SUNSET)
# image living_room_ss_overcast = mas_island_event._apply_flt_on_room_sprite("living_room_day_overcast", mas_sprites.FLT_SUNSET)
# image living_room_ss_snow = mas_island_event._apply_flt_on_room_sprite("living_room_day_snow", mas_sprites.FLT_SUNSET)


# ## Lit room
# # Day images
# image living_room_lit_day = "living_room_day"
# image living_room_lit_day_rain = "living_room_day_rain"
# image living_room_lit_day_overcast = "living_room_day_overcast"
# image living_room_lit_day_snow = "living_room_day_snow"
# # Night images
# image living_room_lit_night = mas_island_event._get_room_sprite("n", True)
# image living_room_lit_night_rain = mas_island_event._get_room_sprite("n_r", True)
# image living_room_lit_night_overcast = "living_room_lit_night_rain"
# image living_room_lit_night_snow = mas_island_event._get_room_sprite("n_s", True)
# # Sunset images
# image living_room_lit_ss = "living_room_ss"
# image living_room_lit_ss_rain = "living_room_ss_rain"
# image living_room_lit_ss_overcast = "living_room_ss_overcast"
# image living_room_lit_ss_snow = "living_room_ss_snow"


# # # Image defination
init -20 python in mas_island_event:
    class IslandsDataDefinition(object):
        """
        A generalised abstraction around raw data for the islands sprites
        """
        TYPE_ISLAND = "island"
        TYPE_DECAL = "decal"
        TYPE_BG = "bg"
        TYPE_OVERLAY = "overlay"
        TYPE_INTERIOR = "interior"
        TYPE_OTHER = "other"# This is basically for everything else
        TYPES = frozenset(
            (
                TYPE_ISLAND,
                TYPE_DECAL,
                TYPE_BG,
                TYPE_OVERLAY,
                TYPE_INTERIOR,
                TYPE_OTHER
            )
        )

        FILENAMES_MAP = {
            TYPE_OVERLAY: ("d", "n"),
        }
        DEF_FILENAMES = ("d", "d_r", "d_s", "n", "n_r", "n_s", "s", "s_r", "s_s")

        DELIM = "_"

        _data_map = dict()

        def __init__(
            self,
            id_,
            type_=None,
            default_unlocked=False,
            filenames=None,
            fp_map=None,
            partial_disp=None
        ):
            """
            Constructor

            IN:
                id_ - unique id for this sprite
                    NOTE: SUPPORTED FORMATS:
                        - 'island_###'
                        - 'decal_###'
                        - 'bg_###'
                        - 'overlay_###'
                        - 'other_###'
                        where ### is something unique
                type_ - type of this sprite, if None, we automatically get it from the id
                    (Default: None)
                default_unlocked - whether or not this sprite is unlocked from the get go
                    (Default: False)
                filenames - the used filenames for this data, those are the keys for fp_map, if None, will be used default
                    paths in the FILENAMES_MAP or DEF_FILENAMES
                    (Default: None)
                fp_map - the map of the images for this sprite, if None, we automatically generate it
                    NOTE: after decoding this will point to a loaded ImageData object instead of a failepath
                    (Default: None)
                partial_disp - functools.partial of the displayable for this sprite
                    (Default: None)
            """
            if self.__split_id(id_)[0] not in self.TYPES:
                raise ValueError(
                    "Bad id format. Supported formats for id: {}, got: '{}'.".format(
                        ", ".join("'{}_###'".format(t) for t in self.TYPES),
                        id_
                    )
                )
            if id_ in self._data_map:
                raise Exception("Id '{}' has already been used.".format(id_))

            self.id = id_

            if type_ is not None:
                if type_ not in self.TYPES:
                    raise ValueError("Bad type. Allowed types: {}, got: '{}'.".format(self.TYPES, type_))

            else:
                type_ = self._getType()

            self.type = type_

            self.default_unlocked = bool(default_unlocked)
            self.filenames = filenames
            self.fp_map = fp_map if fp_map is not None else self._buildFPMap()
            self.partial_disp = partial_disp

            self._data_map[id_] = self

        def _getType(self):
            """
            Private method to get type of this sprite if it hasn't been passed in

            OUT:
                str
            """
            return self._split_id()[0]

        def _buildFPMap(self):
            """
            Private method to build filepath map if one hasn't been passed in

            OUT:
                dict
            """
            filepath_fmt = "{type_}/{name}/{filename}"
            type_, name = self._split_id()
            if self.filenames is None:
                filenames = self.FILENAMES_MAP.get(self.type, self.DEF_FILENAMES)
            else:
                filenames = self.filenames

            # FIXME: Use f-strings with py3 pls
            return {
                filename: filepath_fmt.format(
                    type_=type_,
                    name=name,
                    filename=filename
                )
                for filename in filenames
            }

        def _split_id(self):
            """
            Splits an id into type and name strings
            """
            return self.__split_id(self.id)

        @classmethod
        def __split_id(cls, id_):
            """
            Splits an id into type and name strings
            """
            return id_.split(cls.DELIM, 1)

        @classmethod
        def getDataFor(cls, id_):
            """
            Returns data for an id

            OUT:
                IslandsDataDefinition
                or None
            """
            return cls._data_map.get(id_, None)

        @classmethod
        def getDefaultUnlocks(cls):
            """
            Returns default unlocks for sprites

            OUT:
                dict
            """
            # FIXME: py3 update
            return {
                id_: data.default_unlocked
                for id_, data in cls._data_map.iteritems()
            }

        @classmethod
        def getFilepathsForType(cls, type_):
            """
            Returns filepaths for images of sprites of the given type

            OUT:
                dict
            """
            # FIXME: py3 update
            return {
                id_: data.fp_map
                for id_, data in cls._data_map.iteritems()
                if data.type == type_ and data.fp_map
            }

    # # # Transform funcs for island disps
    # These transforms perform cyclic motion. See dev/transforms for graphical
    # representations of the motions.
    # 'transform' is the transform object we're modifying
    # 'st' and 'at' are not documented, timestamps, we're using 'at' since we're doing animations,
    #     it controls the current position of the object
    # 'amplitude' variables control the maximum extent of the function (basically how far the object can move)
    # 'frequency' variables control the frequency (period) of the function (basically speed of the object)
    # Using different combinations of the functinos and parameters allow to give each object a unique pattern,
    # which will be repeated after some time, creating a seamless loop.
    def __isld_1_transform_func(transform, st, at):
        """
        A function which we use as a transform, updates the child
        """
        amplitude = 0.02
        frequency_1 = 1.0 / 9.0
        frequency_2 = 1.0 / 3.0

        transform.ypos = math.cos(at*frequency_1) * math.sin(at*frequency_2) * amplitude
        # We updated the transform, so we must update the sprite, too
        # But only once the transform is active (otherwise you get a recursive loop)
        if transform.active:
            transform.__parallax_sprite__.update_offsets()

        return 0.0

    def __isld_2_transform_func(transform, st, at):
        """
        A function which we use as a transform, updates the child
        """
        y_amplitude = -0.01
        y_frequency_1 = 0.5
        y_frequency_2 = 0.25

        x_amplitude = -0.0035
        x_frequency = 0.2

        transform.ypos = math.sin(math.sin(at*y_frequency_1) + math.sin(at*y_frequency_2)) * y_amplitude
        transform.xpos = math.cos(at*x_frequency) * x_amplitude
        if transform.active:
            transform.__parallax_sprite__.update_offsets()

        return 0.0

    def __isld_3_transform_func(transform, st, at):
        """
        A function which we use as a transform, updates the child
        """
        amplitude = 0.005
        frequency_1 = 0.25
        frequency_2 = 0.05

        transform.ypos = (math.sin(at*frequency_1) + abs(math.cos(at*frequency_2))) * amplitude
        if transform.active:
            transform.__parallax_sprite__.update_offsets()

        return 0.0

    def __isld_5_transform_func(transform, st, at):
        """
        A function which we use as a transform, updates the child
        """
        y_amplitude = -0.01
        y_frequency_1 = 1.0 / 10.0
        y_frequency_2 = 7.0

        x_amplitude = 0.005
        x_frequency = 0.25

        transform.ypos = math.sin(math.sin(at*y_frequency_1) * y_frequency_2) * y_amplitude
        transform.xpos = math.cos(at*x_frequency) * x_amplitude
        if transform.active:
            transform.__parallax_sprite__.update_offsets()

        return 0.0

    def __chibi_transform_func(transform, st, at):
        """
        A function which we use as a transform, updates the child
        """
        roto_speed = -10
        amplitude = 0.065
        frequency = 0.5

        transform.rotate = at % 360 * roto_speed
        transform.ypos = math.sin(at * frequency) * amplitude
        if transform.active:
            transform.__parallax_sprite__.update_offsets()

        return 0.0

    def _play_thunder(transform, st, at):
        """
        This is used in a transform to play the THUNDER sound effect
        """
        renpy.play("mod_assets/sounds/amb/thunder.wav", channel="backsound")
        return None

    # # # Img definations

    # NOTE: As you can see ParallaxDecal aren't being passed in partials, they are dynamically added later
    # during composite image building
    # NOTE: Use functools.partial instead of renpy.partial because the latter has an argument conflict. Smh Tom
    # Islands
    IslandsDataDefinition(
        "island_0",
        default_unlocked=True,
        partial_disp=functools.partial(
            ParallaxSprite,
            x=-85,
            y=660,
            z=15,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "island_1",
        partial_disp=functools.partial(
            ParallaxSprite,
            x=483,
            y=373,
            z=35,
            function=__isld_1_transform_func,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "island_2",
        partial_disp=functools.partial(
            ParallaxSprite,
            x=275,
            y=299,
            z=70,
            function=__isld_2_transform_func,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "island_3",
        partial_disp=functools.partial(
            ParallaxSprite,
            x=292,
            y=155,
            z=95,
            function=__isld_3_transform_func,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "island_4",
        partial_disp=functools.partial(
            ParallaxSprite,
            x=-15,
            y=-15,
            z=125,
            on_click="mas_island_upsidedownisland"
        )
    )
    IslandsDataDefinition(
        "island_5",
        partial_disp=functools.partial(
            ParallaxSprite,
            x=991,
            y=184,
            z=55,
            function=__isld_5_transform_func,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "island_6",
        partial_disp=functools.partial(
            ParallaxSprite,
            x=912,
            y=46,
            z=200,
            function=None,
            on_click="mas_island_distant_islands"
        )
    )
    IslandsDataDefinition(
        "island_7",
        partial_disp=functools.partial(
            ParallaxSprite,
            x=439,
            y=84,
            z=250,
            function=None,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "island_8",
        partial_disp=functools.partial(
            ParallaxSprite,
            x=484,
            y=54,
            z=220,
            on_click="mas_island_distant_islands"
        )
    )

    # Decals
    IslandsDataDefinition(
        "decal_bookshelf",
        partial_disp=functools.partial(
            ParallaxDecal,
            x=358,
            y=62,
            z=6,
            on_click="mas_island_bookshelf"
        )
    )
    IslandsDataDefinition(
        "decal_bushes",
        partial_disp=functools.partial(
            ParallaxDecal,
            x=305,
            y=70,
            z=8,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "decal_house",
        partial_disp=functools.partial(
            ParallaxDecal,
            x=215,
            y=-37,
            z=1
        )
    )
    IslandsDataDefinition(
        "decal_tree",
        partial_disp=functools.partial(
            ParallaxDecal,
            x=130,
            y=-194,
            z=4,
            on_click="mas_island_cherry_blossom_tree"
        )
    )
    GLITCH_FPS = (
        "other/glitch/frame_0",
        "other/glitch/frame_1",
        "other/glitch/frame_2",
        "other/glitch/frame_3",
        "other/glitch/frame_4",
        "other/glitch/frame_5",
        "other/glitch/frame_6"
    )
    IslandsDataDefinition(
        "decal_glitch",
        fp_map={},# TODO: move GLITCH_FPS to fp_map
        partial_disp=functools.partial(
            ParallaxDecal,
            x=216,
            y=-54,
            z=2,
            on_click="mas_island_glitchedmess"
        )
    )
    # O31 specific decals
    IslandsDataDefinition(
        "decal_bloodfall",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=213,
            y=0,
            z=1,
            on_click="mas_island_bloodfall"
        )
    )
    IslandsDataDefinition(
        "decal_ghost_0",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=366,
            y=-48,
            z=5,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "decal_ghost_1",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=366,
            y=-48,
            z=5,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "decal_ghost_2",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=366,
            y=-48,
            z=5,
            on_click=True
        )
    )
    # NOTE: these trees have same params as decal_tree
    IslandsDataDefinition(
        "decal_haunted_tree_0",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=130,
            y=-194,
            z=4,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "decal_haunted_tree_1",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=130,
            y=-194,
            z=4,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "decal_haunted_tree_2",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=130,
            y=-194,
            z=4,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "decal_gravestones",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=123,
            y=17,
            z=1,
            on_click="mas_island_gravestones"
        )
    )
    IslandsDataDefinition(
        "decal_jack",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=253,
            y=63,
            z=2,
            on_click="mas_island_pumpkins"
        )
    )
    IslandsDataDefinition(
        "decal_pumpkins",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=178,
            y=59,
            z=15,
            on_click="mas_island_pumpkins"
        )
    )
    IslandsDataDefinition(
        "decal_skull",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=120,
            y=-10,
            z=1,
            on_click=True
        )
    )
    IslandsDataDefinition(
        "decal_webs",
        filenames=("d", "n"),
        partial_disp=functools.partial(
            ParallaxDecal,
            x=187,
            y=-99,
            z=5,
            # on_click=True
        )
    )

    # Objects
    IslandsDataDefinition(
        "other_shimeji",
        fp_map={},
        partial_disp=functools.partial(
            ParallaxSprite,
            Transform(renpy.easy.displayable("chibika smile"), zoom=0.3),
            x=930,
            y=335,
            z=36,
            function=__chibi_transform_func,
            on_click="mas_island_shimeji"
        )
    )
    # IslandsDataDefinition(
    #     "other_isly",
    #     filenames=("clear", "rain", "snow")
    # )

    # # Interior
    # IslandsDataDefinition(
    #     "interior_room",
    #     filenames=("d", "d_r", "d_s", "n", "n_r", "n_s")
    # )
    # IslandsDataDefinition(
    #     "interior_room_lit",
    #     filenames=("d", "d_r", "d_s", "n", "n_r", "n_s")
    # )
    # IslandsDataDefinition(
    #     "interior_tablechair",
    #     filenames=("chair", "shadow", "table")
    # )

    # BGs
    IslandsDataDefinition(
        "bg_def",
        default_unlocked=True,
        partial_disp=functools.partial(
            ParallaxSprite,
            x=0,
            y=0,
            z=15000,
            min_zoom=1.02,
            max_zoom=4.02,
            on_click="mas_island_sky"
        )
    )

    # Overlays
    IslandsDataDefinition(
        "overlay_rain",
        default_unlocked=True,
        partial_disp=functools.partial(
            _build_weather_overlay_transform,
            speed=0.8
        )
    )
    IslandsDataDefinition(
        "overlay_snow",
        default_unlocked=True,
        partial_disp=functools.partial(
            _build_weather_overlay_transform,
            speed=3.5
        )
    )
    IslandsDataDefinition(
        "overlay_thunder",
        default_unlocked=True,
        fp_map={},
        partial_disp=functools.partial(
            renpy.easy.displayable,
            "mas_islands_lightning_overlay"
        )
    )
    IslandsDataDefinition(
        "overlay_vignette",
        default_unlocked=True
    )


# # # Main framework
init -25 python in mas_island_event:
    import random
    import functools
    import math
    import io
    from zipfile import ZipFile
    import datetime

    import store
    from store import (
        persistent,
        mas_utils,
        mas_weather,
        mas_sprites,
        mas_ics,
        Transform,
        LiveComposite,
        MASWeatherMap,
        MASFilterWeatherDisplayableCustom,
        MASFilterWeatherDisplayable
    )
    from store.mas_parallax import (
        ParallaxBackground,
        ParallaxSprite,
        ParallaxDecal
    )

    DEF_PROGRESS = -1
    MAX_PROGRESS_ENAM = 4
    MAX_PROGRESS_LOVE = 8
    PROGRESS_FACTOR = 4

    SHIMEJI_CHANCE = 0.01
    DEF_SCREEN_ZORDER = 55

    SUPPORTED_FILTERS = frozenset(
        {
            mas_sprites.FLT_DAY,
            mas_sprites.FLT_NIGHT,
            mas_sprites.FLT_SUNSET
        }
    )

    DATA_ITS_JUST_MONIKA = b"JUSTMONIKA"*1024
    DATA_JM_SIZE = len(DATA_ITS_JUST_MONIKA)
    DATA_READ_CHUNK_SIZE = 2 * 1024**2
    DATA_SPACING = 8 * 1024**2

    REVEAL_FADEIN_TIME = 0.5
    REVEAL_WAIT_TIME = 0.1
    REVEAL_FADEOUT_TIME = REVEAL_FADEIN_TIME

    REVEAL_TRANSITION_TIME = REVEAL_FADEIN_TIME + REVEAL_WAIT_TIME + REVEAL_FADEOUT_TIME
    REVEAL_ANIM_DELAY = REVEAL_FADEIN_TIME + REVEAL_WAIT_TIME

    REVEAL_ANIM_1_DURATION = 12.85
    REVEAL_ANIM_2_DURATION = 13.1
    REVEAL_ANIM_3_1_DURATION = 13.6
    REVEAL_ANIM_3_2_DURATION = 12.7
    REVEAL_ANIM_4_DURATION = 0.5

    REVEAL_OVERVIEW_DURATION = 10.0

    REVEAL_FADE_TRANSITION = store.Fade(REVEAL_FADEIN_TIME, REVEAL_WAIT_TIME, REVEAL_FADEOUT_TIME)
    REVEAL_DISSOLVE_TRANSITION = store.Dissolve(REVEAL_FADEIN_TIME)

    SFX_LIT = "_lit"
    SFX_NIGHT = "_night"

    LIVING_ROOM_ID = "living_room"
    LIVING_ROOM_LIT_ID = LIVING_ROOM_ID + SFX_LIT

    FLT_LR_NIGHT = LIVING_ROOM_ID + SFX_NIGHT
    mas_sprites.add_filter(
        FLT_LR_NIGHT,
        store.im.matrix.tint(0.421, 0.520, 0.965),
        mas_sprites.FLT_NIGHT
    )
    FLT_LR_LIT_NIGHT = LIVING_ROOM_LIT_ID + SFX_NIGHT
    mas_sprites.add_filter(
        FLT_LR_LIT_NIGHT,
        store.im.matrix.tint(0.972, 0.916, 0.796),
        mas_sprites.FLT_NIGHT
    )

    # These're being populated later once we decode the imgs
    island_disp_map = dict()
    decal_disp_map = dict()
    other_disp_map = dict()
    bg_disp_map = dict()
    overlay_disp_map = dict()
    interior_disp_map = dict()

    NULL_DISP = store.Null()

    # setup the docking station we are going to use here
    islands_station = store.MASDockingStation(mas_ics.ISLANDS_FOLDER)

    def isFilterSupported(flt):
        """
        Checks if the event supports a filter

        IN:
            flt - the filter to check (perhaps one of the constants in mas_sprites)

        OUT:
            boolean
        """
        return flt in SUPPORTED_FILTERS

    def _select_img(st, at, mfwm):
        """
        Selection function to use in Island-based images

        IN:
            st - renpy related
            at - renpy related
            mfwm - MASFilterWeatherMap for this island

        RETURNS:
            displayable data
        """
        # During winter we always return images with snow
        # Nonideal, but we have to do this because of the tree
        # FIXME: ideal solution would be split the images by seasons too
        if store.mas_isWinter():
            return mfwm.fw_get(mas_sprites.get_filter(), store.mas_weather_snow), None

        return store.mas_fwm_select(st, at, mfwm)

    def IslandFilterWeatherDisplayable(**filter_pairs):
        """
        DynamicDisplayable for Island images.

        IN:
            **filter_pairs - filter pairs to MASFilterWeatherMap.

        OUT:
            DynamicDisplayable for Island images that respect filters and
                weather.
        """
        return MASFilterWeatherDisplayableCustom(
            _select_img,
            True,
            **filter_pairs
        )

    def _handle_raw_pkg_data(pkg_data, base_err_msg):
        """
        Handles raw data and returns clean, parsed data
        Logs errors

        IN:
            pkg_data - memory buffer

        OUT:
            memory buffer or None
        """
        buf = io.BytesIO()
        buf.seek(0)
        pkg_data.seek(0)

        try:
            while True:
                this_slice_read = 0
                pkg_data.seek(DATA_JM_SIZE, io.SEEK_CUR)

                while this_slice_read < DATA_SPACING:
                    chunk = pkg_data.read(DATA_READ_CHUNK_SIZE)
                    chunk_size = len(chunk)

                    if not chunk_size:
                        buf.seek(0)
                        return buf

                    this_slice_read += chunk_size
                    buf.write(chunk)

        except Exception as e:
            mas_utils.mas_log.error(
                base_err_msg.format(
                    "Unexpected exception while parsing raw package data: {}".format(e)
                )
            )
            return None

        buf.seek(0)
        return buf

    def decode_data():
        """
        Attempts to decode the images

        OUT:
            True upon success, False otherwise
        """
        err_msg = "Failed to decode isld data: {}.\n"

        pkg = islands_station.getPackage("our_reality")

        if not pkg:
            mas_utils.mas_log.error(err_msg.format("Missing package"))
            return False

        pkg_data = islands_station.unpackPackage(pkg, pkg_slip=mas_ics.ISLAND_PKG_CHKSUM)

        if not pkg_data:
            mas_utils.mas_log.error(err_msg.format("Bad package"))
            return False

        zip_data = _handle_raw_pkg_data(pkg_data, err_msg)
        if not zip_data:
            return False

        glitch_frames = None

        def _read_zip(zip_file, map_):
            """
            Inner helper function to read zip and override maps

            IN:
                zip_file - the zip file opened for reading
                map_ - the map to get filenames from, and which will be overriden
            """
            # FIXME: py3 update
            for name, path_map in map_.iteritems():
                for sprite_type, path in path_map.iteritems():
                    raw_data = zip_file.read(path)
                    img = store.MASImageData(raw_data, "{}_{}.png".format(name, sprite_type))
                    path_map[sprite_type] = img

        try:
            with ZipFile(zip_data, "r") as zip_file:
                island_map = IslandsDataDefinition.getFilepathsForType(IslandsDataDefinition.TYPE_ISLAND)
                decal_map = IslandsDataDefinition.getFilepathsForType(IslandsDataDefinition.TYPE_DECAL)
                bg_map = IslandsDataDefinition.getFilepathsForType(IslandsDataDefinition.TYPE_BG)
                overlay_map = IslandsDataDefinition.getFilepathsForType(IslandsDataDefinition.TYPE_OVERLAY)
                interior_map = IslandsDataDefinition.getFilepathsForType(IslandsDataDefinition.TYPE_INTERIOR)
                # Now override maps to contain imgs instead of img paths
                for map_ in (island_map, decal_map, bg_map, overlay_map, interior_map):
                    _read_zip(zip_file, map_)

                # Anim frames are handled a bit differently
                glitch_frames = tuple(
                    (store.MASImageData(zip_file.read(fn), fn + ".png") for fn in GLITCH_FPS)
                )

                # Audio is being loaded right away
                isly_data = IslandsDataDefinition.getDataFor("other_isly")
                if isly_data:
                    for fn, fp in isly_data.fp_map.iteritems():
                        audio_data = store.MASAudioData(zip_file.read(fp), fp + ".ogg")
                        setattr(store.audio, "isld_isly_" + fn, audio_data)

        except Exception as e:
            mas_utils.mas_log.error(err_msg.format(e), exc_info=True)
            return False

        else:
            # We loaded the images, now create dynamic displayables
            _build_displayables(island_map, decal_map, bg_map, overlay_map, interior_map, glitch_frames)

        return True

    def _build_filter_pairs(img_map):
        """
        Builds filter pairs for IslandFilterWeatherDisplayable
        or MASFilterWeatherDisplayable
        """
        precip_to_suffix_map = {
            mas_weather.PRECIP_TYPE_DEF: "",
            mas_weather.PRECIP_TYPE_RAIN: "_r",
            mas_weather.PRECIP_TYPE_SNOW: "_s",
            mas_weather.PRECIP_TYPE_OVERCAST: "_r"# reuse rain
        }

        def _create_weather_map(main_key):
            if main_key not in img_map:
                return None

            precip_map = {}

            for p_type, suffix in precip_to_suffix_map.iteritems():
                k = main_key + suffix
                if k in img_map:
                    precip_map[p_type] = img_map[k]

            if not precip_map:
                raise Exception("Failed to make precip map for: {}".format(img_map))

            return MASWeatherMap(precip_map)

        filter_keys = ("day", "night", "sunset")
        filter_pairs = {}

        for k in filter_keys:
            wm = _create_weather_map(k[0])
            if wm is not None:
                filter_pairs[k] = wm

        return filter_pairs

    def _build_ifwd(img_map):
        """
        Builds a single IslandFilterWeatherDisplayable
        using the given image map
        """
        filter_pairs = _build_filter_pairs(img_map)
        return IslandFilterWeatherDisplayable(**filter_pairs)

    def _build_fwd(img_map):
        """
        Builds a single MASFilterWeatherDisplayable
        using the given image map
        """
        filter_pairs = _build_filter_pairs(img_map)
        return MASFilterWeatherDisplayable(use_fb=True, **filter_pairs)

    def _build_weather_overlay_transform(child, speed):
        """
        A wrapper around mas_islands_weather_overlay_transform
        It exists so we can properly pass the child argument
        to the transform
        """
        return store.mas_islands_weather_overlay_transform(
            child=child,
            speed=speed
        )

    def _build_displayables(
        island_imgs_maps,
        decal_imgs_maps,
        bg_imgs_maps,
        overlay_imgs_maps,
        interior_imgs_map,
        glitch_frames
    ):
        """
        Takes multiple maps with images and builds displayables from them, sets global vars
        NOTE: no sanity checks
        FIXME: py3 update

        IN:
            island_imgs_maps - the map from island names to raw images map
            decal_imgs_maps - the map from decal names to raw images map
            bg_imgs_maps - the map from bg ids to raw images map
            overlay_imgs_maps - the map from overlay ids to raw images map
            interior_imgs_map - the map from the interior stuff to the raw images map
            glitch_frames - tuple of glitch raw anim frames
        """
        global island_disp_map, decal_disp_map, other_disp_map
        global bg_disp_map, overlay_disp_map, interior_disp_map

        # Build the islands
        for island_name, img_map in island_imgs_maps.iteritems():
            disp = _build_ifwd(img_map)
            partial_disp = IslandsDataDefinition.getDataFor(island_name).partial_disp
            island_disp_map[island_name] = partial_disp(disp)

        # Build the decals
        for decal_name, img_map in decal_imgs_maps.iteritems():
            disp = _build_ifwd(img_map)
            partial_disp = IslandsDataDefinition.getDataFor(decal_name).partial_disp
            decal_disp_map[decal_name] = partial_disp(disp)

        # Build the bg
        for bg_name, img_map in bg_imgs_maps.iteritems():
            disp = _build_ifwd(img_map)
            partial_disp = IslandsDataDefinition.getDataFor(bg_name).partial_disp
            bg_disp_map[bg_name] = partial_disp(disp)

        # Build the overlays
        for overlay_name, img_map in overlay_imgs_maps.iteritems():
            disp = _build_fwd(img_map)
            partial_disp = IslandsDataDefinition.getDataFor(overlay_name).partial_disp
            if partial_disp is not None:
                disp = partial_disp(disp)
            overlay_disp_map[overlay_name] = disp

        # Build the interior
        for name, img_map in interior_imgs_map.iteritems():
            interior_disp_map[name] = img_map

        if interior_disp_map:
            # HACK: add custom tablechair into the cache right here
            # That's because our images are not on the disk, we can't just use a sprite tag
            # because the paths are hardcoded and we can't use a displayable directly
            for flt_id in (FLT_LR_NIGHT, FLT_LR_LIT_NIGHT):
                tablechair_disp_cache = mas_sprites.CACHE_TABLE[mas_sprites.CID_TC]
                table_im = mas_sprites._gen_im(
                    flt_id,
                    interior_disp_map["interior_tablechair"]["table"]
                )
                tablechair_disp_cache[(flt_id, 0, LIVING_ROOM_ID, 0)] = table_im
                tablechair_disp_cache[(flt_id, 0, LIVING_ROOM_ID, 1)] = table_im# shadow variant can reuse the same img
                tablechair_disp_cache[(flt_id, 1, LIVING_ROOM_ID)] = mas_sprites._gen_im(
                    flt_id,
                    interior_disp_map["interior_tablechair"]["chair"]
                )
                # Shadow is being stored in the highlight cache
                table_shadow_hl_disp_cache = mas_sprites.CACHE_TABLE[mas_sprites.CID_HL]
                table_shadow_hl_disp_cache[(mas_sprites.CID_TC, flt_id, 0, LIVING_ROOM_ID, 1)] = interior_disp_map["interior_tablechair"]["shadow"]

        # Build glitch disp
        def _glitch_transform_func(transform, st, at):
            """
            A function which we use as a transform, updates the child
            """
            redraw = random.uniform(0.3, 1.3)
            next_child = random.choice(glitch_frames)

            transform.child = next_child

            return redraw

        glitch_disp = Transform(child=glitch_frames[0], function=_glitch_transform_func)
        partial_disp = IslandsDataDefinition.getDataFor("decal_glitch").partial_disp
        decal_disp_map["decal_glitch"] = partial_disp(glitch_disp)

        # Build chibi disp
        partial_disp = IslandsDataDefinition.getDataFor("other_shimeji").partial_disp
        other_disp_map["other_shimeji"] = partial_disp()

        # Build thunder overlay
        partial_disp = IslandsDataDefinition.getDataFor("overlay_thunder").partial_disp
        overlay_disp_map["overlay_thunder"] = partial_disp()

        return

    def _get_room_sprite(key, is_lit):
        """
        Returns the appropriate displayable for the room sprite based on the criteria

        IN:
            key - str - the sprite key
            is_lit - bool - sprite for the lit or unlit version?

        OUT:
            MASImageData
            or Null displayable if we failed to get the image
        """
        main_key = "interior_room" if not is_lit else "interior_room_lit"
        try:
            return interior_disp_map[main_key][key]

        except KeyError:
            return NULL_DISP

    def _apply_flt_on_room_sprite(room_img_tag, flt):
        """
        Returns the room image with the filter applied on it

        IN:
            room_img_tag - str - the image tag
            flt - str - the filter id to use

        OUT:
            image manipulator
            or Null displayable if we failed to decode the images
        """
        if not store.mas_decoded_islands:
            return NULL_DISP

        return store.MASFilteredSprite(
            flt,
            renpy.displayable(room_img_tag)
        )

    def _is_unlocked(id_):
        """
        Checks if a sprite is unlocked

        IN:
            id_ - the unique id of the sprite

        OUT:
            boolean
        """
        return persistent._mas_islands_unlocks.get(id_, False)

    def _unlock(id_):
        """
        Unlocks a sprite

        IN:
            id_ - the unique id of the sprite

        OUT:
            boolean whether or not the sprite was unlocked
        """
        if id_ in persistent._mas_islands_unlocks:
            persistent._mas_islands_unlocks[id_] = True
            return True

        return False

    def _lock(id_):
        """
        Locks a sprite

        IN:
            id_ - the unique id of the sprite

        OUT:
            boolean whether or not the sprite was locked
        """
        if id_ in persistent._mas_islands_unlocks:
            persistent._mas_islands_unlocks[id_] = False
            return True

        return False

    def _unlock_one(*items):
        """
        Unlocks one of the sprites at random.
        Runs only once

        IN:
            *items - the ids of the sprites

        OUT:
            boolean whether or not a sprite was unlocked
        """
        for i in items:
            if _is_unlocked(i):
                return False

        return _unlock(random.choice(items))


    # # # START functions for lvl unlocks
    def __unlocks_for_lvl_0():
        _unlock("island_1")
        _unlock("island_8")

    def __unlocks_for_lvl_1():
        _unlock("other_shimeji")
        if not renpy.seen_label("mas_monika_islands_final_reveal"):
            _unlock("decal_glitch")
        _unlock("decal_pumpkins")
        _unlock("decal_skull")

    def __unlocks_for_lvl_2():
        _unlock("island_2")

    def __unlocks_for_lvl_3():
        # Unlock only one, the rest at lvl 6
        _unlock_one("island_4", "island_5")

    def __unlocks_for_lvl_4():
        # Unlock only one, the rest at lvl 7
        _unlock_one("island_6", "island_7")

    def __unlocks_for_lvl_5():
        # This requires the 4th isld
        if _is_unlocked("island_4"):
            _unlock("decal_bloodfall")
        # This requires the 5th isld
        if _is_unlocked("island_5"):
            _unlock("decal_gravestones")

    def __unlocks_for_lvl_6():
        _unlock("decal_bushes")
        # Unlock everything from lvl 3
        _unlock("island_4")
        _unlock("island_5")

    def __unlocks_for_lvl_7():
        _unlock("island_3")
        # Unlock only one, the rest at lvl 7
        _unlock_one("decal_bookshelf", "decal_tree")
        # These require the tree
        if _is_unlocked("decal_tree"):
            _unlock_one(*("decal_ghost_" + i for i in "012"))
        # Unlock everything from lvl 4
        _unlock("island_7")
        _unlock("island_6")

    def __unlocks_for_lvl_8():
        # Unlock everything from lvl 7
        _unlock("decal_bookshelf")
        _unlock("decal_tree")
        # These require the tree
        for i in "012":
            _unlock("decal_haunted_tree_" + i)

    def _final_unlocks():
        # TODO: update monika_why_spaceroom
        # NOTE: NO SANITY CHECKS, use carefully
        _unlock("other_isly")
        _unlock("decal_house")
        # These requires the house
        _unlock("decal_jack")
        _unlock("decal_webs")
        _lock("decal_glitch")

    def __unlocks_for_lvl_9():
        if persistent._mas_pm_cares_island_progress is not False:
            if renpy.seen_label("mas_monika_islands_final_reveal"):
                _final_unlocks()

            else:
                pass

    def __unlocks_for_lvl_10():
        if persistent._mas_pm_cares_island_progress is False:
            if renpy.seen_label("mas_monika_islands_final_reveal"):
                _final_unlocks()

            else:
                pass

    # # # END


    def __handle_unlocks():
        """
        Method to unlock various islands features when the player progresses.
        For example: new decals, new islands, new extra events, set persistent vars, etc.
        """
        g = globals()
        for i in range(persistent._mas_islands_progress + 1):
            fn_name = renpy.munge("__unlocks_for_lvl_{}".format(i))
            callback = g.get(fn_name, None)
            if callback is not None:
                callback()

    def _calc_progress(curr_lvl, start_lvl):
        """
        Returns islands progress for the given current and start levels
        NOTE: this has no sanity checks, don't use this directly

        IN:
            curr_lvl - int, current level
            start_lvl - int, start level

        OUT:
            int, progress
        """
        lvl_difference = curr_lvl - start_lvl

        if lvl_difference < 0:
            return DEF_PROGRESS

        if store.mas_isMoniEnamored(higher=True):
            if store.mas_isMoniLove(higher=True):
                max_progress = MAX_PROGRESS_LOVE

            else:
                max_progress = MAX_PROGRESS_ENAM

            modifier = 1.0

            if persistent._mas_pm_cares_island_progress is True:
                modifier -= 0.2

            elif persistent._mas_pm_cares_island_progress is False:
                modifier += 0.3

            progress_factor = PROGRESS_FACTOR * modifier

            progress = min(int(lvl_difference / progress_factor), max_progress)

        else:
            progress = DEF_PROGRESS

        return progress

    def advance_progression():
        """
        Increments the lvl of progression of the islands event,
        it will do nothing if the player hasn't unlocked the islands yet or if
        the current lvl is invalid
        """
        # If this var is None, then the user hasn't unlocked the event yet
        if persistent._mas_islands_start_lvl is None:
            return

        new_progress = _calc_progress(store.mas_xp.level(), persistent._mas_islands_start_lvl)

        if new_progress == DEF_PROGRESS:
            return

        curr_progress = persistent._mas_islands_progress
        # I hate this, but we have to push the ev from here
        if (
            # Has progress means has new unlocks
            new_progress > curr_progress
            # Not the first lvls, not the last lvl
            and DEF_PROGRESS + 1 < new_progress < MAX_PROGRESS_LOVE - 1
            # Hasn't seen the event yet
            and persistent._mas_pm_cares_island_progress is None
            and not store.seen_event("mas_monika_islands_progress")
            # Hasn't visited the islands for a few days
            and store.mas_timePastSince(store.mas_getEVL_last_seen("mas_monika_islands"), datetime.timedelta(days=1))
        ):
            store.MASEventList.push("mas_monika_islands_progress")

        # Now set new level
        persistent._mas_islands_progress = min(max(new_progress, curr_progress), MAX_PROGRESS_LOVE)
        # Run unlock callbacks
        __handle_unlocks()

        return

    def _get_progression():
        """
        Returns current islands progress lvl
        """
        return persistent._mas_islands_progress

    def start_progression():
        """
        Starts islands progression
        """
        if store.mas_isMoniEnamored(higher=True) and persistent._mas_islands_start_lvl is None:
            persistent._mas_islands_start_lvl = store.mas_xp.level()
            advance_progression()

    def _reset_progression():
        """
        Resets island progress
        """
        persistent._mas_islands_start_lvl = None
        persistent._mas_islands_progress = DEF_PROGRESS
        persistent._mas_islands_unlocks = IslandsDataDefinition.getDefaultUnlocks()

    def play_music():
        """
        Plays appropriate music based on the current weather
        """
        if not _is_unlocked("other_isly"):
            return

        if store.mas_is_raining:
            track = store.audio.isld_isly_rain

        elif store.mas_is_snowing:
            track = store.audio.isld_isly_snow

        else:
            track = store.audio.isld_isly_clear

        if track:
            store.mas_play_song(track, loop=True, set_per=False, fadein=2.5, fadeout=2.5)

    def stop_music():
        """
        Stops islands music
        """
        if store.songs.current_track in (
            store.audio.isld_isly_rain,
            store.audio.isld_isly_snow,
            store.audio.isld_isly_clear
        ):
            store.mas_play_song(None, fadeout=2.5)

    def get_islands_displayable(enable_interaction=True, check_progression=False):
        """
        Builds an image for islands and returns it
        NOTE: This is temporary until we split islands into foreground/background
        FIXME: py3 update

        IN:
            enable_interaction - whether to enable events or not (including parallax effect)
                (Default: True)
            check_progression - whether to check for new unlocks or not,
                this might be a little slow
                (Default: False)

        OUT:
            ParallaxBackground
        """
        global SHIMEJI_CHANCE

        enable_o31_deco = persistent._mas_o31_in_o31_mode and not is_winter_weather()

        def _reset_parallax_disp(disp):
            # Just in case we always remove all decals and readd them as needed
            disp.clear_decals()
            # Toggle events as desired
            disp.toggle_events(enable_interaction)
            # Reset offsets and zoom
            disp.reset_mouse_pos()
            disp.zoom = disp.min_zoom
            # Return it for convenience
            return disp

        # Progress lvl
        if check_progression:
            advance_progression()

        # Add all unlocked islands
        sub_displayables = [
            _reset_parallax_disp(disp)
            for key, disp in island_disp_map.iteritems()
            if _is_unlocked(key)
        ]

        # Add all unlocked decals for islands 1
        isld_1_decals = ["decal_bookshelf", "decal_bushes", "decal_house", "decal_glitch"]
        if not enable_o31_deco:# O31 has a different tree
            isld_1_decals.append("decal_tree")

        island_disp_map["island_1"].add_decals(
            *(
                decal_disp_map[key]
                for key in isld_1_decals
                if _is_unlocked(key)
            )
        )

        # Now add all unlocked O31 decals
        if enable_o31_deco:
            # Basic decals
            isld_to_decals_map = {
                "island_0": ("decal_skull",),
                "island_1": (
                    "decal_ghost_0",
                    "decal_ghost_1",
                    "decal_ghost_2",
                    "decal_jack",
                    "decal_pumpkins",
                    "decal_webs"
                ),
                "island_5": ("decal_gravestones",)
            }
            for isld, decals in isld_to_decals_map.iteritems():
                island_disp_map[isld].add_decals(
                    *(decal_disp_map[key] for key in decals if _is_unlocked(key))
                )

            # The tree has extra logic
            if store.mas_current_background.isFltDay() or not is_cloudy_weather():
                if random.random() < 0.5:
                    haunted_tree = "decal_haunted_tree_0"
                else:
                    haunted_tree = "decal_haunted_tree_1"
            else:
                haunted_tree = "decal_haunted_tree_2"

            if _is_unlocked(haunted_tree):
                island_disp_map["island_1"].add_decals(decal_disp_map[haunted_tree])

            # The bloodfall has extra condition
            if store.mas_current_background.isFltNight() and _is_unlocked("decal_bloodfall"):
                island_disp_map["island_4"].add_decals(decal_disp_map["decal_bloodfall"])

        if _is_unlocked("other_shimeji") and random.random() <= SHIMEJI_CHANCE:
            shimeji_disp = other_disp_map["other_shimeji"]
            _reset_parallax_disp(shimeji_disp)
            SHIMEJI_CHANCE /= 2.0
            sub_displayables.append(shimeji_disp)

        # Add the bg (we only have one as of now)
        bg_disp = bg_disp_map["bg_def"]
        _reset_parallax_disp(bg_disp)
        sub_displayables.append(bg_disp)

        # Sort in order from back to front
        sub_displayables.sort(key=lambda sprite: sprite.z, reverse=True)

        # Now add overlays (they are always last)
        if store.mas_is_raining:
            sub_displayables.append(overlay_disp_map["overlay_rain"])
            if store.mas_globals.show_lightning:
                sub_displayables.insert(1, overlay_disp_map["overlay_thunder"])

        elif store.mas_is_snowing:
            sub_displayables.append(overlay_disp_map["overlay_snow"])

        # NOTE: Vignette is above EVERYTHING else and works even during the snow
        if persistent._mas_o31_in_o31_mode:
            sub_displayables.append(overlay_disp_map["overlay_vignette"])

        return ParallaxBackground(*sub_displayables)

    def is_winter_weather():
        """
        Checks if the weather on the islands is wintery

        OUT:
            boolean:
                - True if we're using snow islands
                - False otherwise
        """
        return store.mas_is_snowing or store.mas_isWinter()

    def is_cloudy_weather():
        """
        Checks if the weather on the islands is cloudy

        OUT:
            boolean:
                - True if we're using overcast/rain islands
                - False otherwise
        """
        return store.mas_is_raining or store.mas_current_weather == store.mas_weather_overcast


init -1 python in mas_island_event:
    from store import (
        MASFilterableBackground,
        MASFilterWeatherMap,
        MASBackgroundFilterManager,
        MASBackgroundFilterChunk,
        MASBackgroundFilterSlice
    )

    def _living_room_entry(_old, **kwargs):
        """
        Entry pp for lr background
        """
        store.monika_chr.tablechair.table = "living_room"
        store.monika_chr.tablechair.chair = "living_room"


    def _living_room_exit(_new, **kwargs):
        """
        Exit pp for lr background
        """
        store.monika_chr.tablechair.table = "def"
        store.monika_chr.tablechair.chair = "def"

    def register_room(id_):
        """
        Registers lr as a background object

        IN:
            id_ - the id to register under

        OUT:
            MASFilterableBackground
        """
        flt_name_night = id_ + SFX_NIGHT
        mfwm_params = {
            "day": MASWeatherMap(
                {
                    mas_weather.PRECIP_TYPE_DEF: id_ + "_day",
                    mas_weather.PRECIP_TYPE_RAIN: id_ + "_day_rain",
                    mas_weather.PRECIP_TYPE_OVERCAST: id_ + "_day_overcast",
                    mas_weather.PRECIP_TYPE_SNOW: id_ + "_day_snow"
                }
            ),
            "sunset": MASWeatherMap(
                {
                    mas_weather.PRECIP_TYPE_DEF: id_ + "_ss",
                    mas_weather.PRECIP_TYPE_RAIN: id_ + "_ss_rain",
                    mas_weather.PRECIP_TYPE_OVERCAST: id_ + "_ss_overcast",
                    mas_weather.PRECIP_TYPE_SNOW: id_ + "_ss_snow"
                }
            )
        }
        mfwm_params[flt_name_night] = MASWeatherMap(
            {
                mas_weather.PRECIP_TYPE_DEF: id_ + "_night",
                mas_weather.PRECIP_TYPE_RAIN: id_ + "_night_rain",
                mas_weather.PRECIP_TYPE_OVERCAST: id_ + "_night_overcast",
                mas_weather.PRECIP_TYPE_SNOW: id_ + "_night_snow"
            }
        )

        return MASFilterableBackground(
            id_,
            "Living room",
            MASFilterWeatherMap(**mfwm_params),
            MASBackgroundFilterManager(
                MASBackgroundFilterChunk(
                    False,
                    None,
                    MASBackgroundFilterSlice.cachecreate(
                        id_ + SFX_NIGHT,
                        60,
                        None,
                        10
                    )
                ),
                MASBackgroundFilterChunk(
                    True,
                    None,
                    MASBackgroundFilterSlice.cachecreate(
                        mas_sprites.FLT_SUNSET,
                        60,
                        30*60,
                        10
                    ),
                    MASBackgroundFilterSlice.cachecreate(
                        mas_sprites.FLT_DAY,
                        60,
                        None,
                        10
                    ),
                    MASBackgroundFilterSlice.cachecreate(
                        mas_sprites.FLT_SUNSET,
                        60,
                        30*60,
                        10
                    )
                ),
                MASBackgroundFilterChunk(
                    False,
                    None,
                    MASBackgroundFilterSlice.cachecreate(
                        id_ + SFX_NIGHT,
                        60,
                        None,
                        10
                    )
                )
            ),
            hide_calendar=True,
            unlocked=False,
            entry_pp=_living_room_entry,
            exit_pp=_living_room_exit
        )


init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_monika_islands",
            category=['моника','разное'],
            prompt="Можешь показать мне летающие острова?",
            pool=True,
            unlocked=False,
            rules={"no_unlock": None, "bookmark_rule": store.mas_bookmarks_derand.WHITELIST},
            aff_range=(mas_aff.ENAMORED, None),
            flags=EV_FLAG_DEF if mas_canShowIslands(False) else EV_FLAG_HFM
        ),
        restartBlacklist=True
    )

label mas_monika_islands:
    m 1eub "Конечно! Ты можешь полюбоваться пейзажем."

    call mas_islands(force_exp="monika 1eua", scene_change=True)

    m 1eua "Надеюсь, тебе понравилось, [mas_get_player_nickname()]~"
    return

default persistent._mas_pm_cares_island_progress = None
# pm var re: player caring about Moni's island progress

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_monika_islands_progress"
        ),
        restartBlacklist=True
    )

label mas_monika_islands_progress:
    m 1eub "[player], у меня для тебя интересные новости!"
    m 3hub "Я сделала несколько новых дополнений на островах, {w=0.2}{nw}"
    extend 1rua "и я подумала, может быть, ты захочешь взглянуть."
    m 1hublb "В конце концов, это же {i}наши{/i} острова~"

    m 3eua "Что ты скажешь?{nw}"
    $ _history_list.pop()
    menu:
        m "Что ты скажешь?{fast}"

        "Конечно, [m_name].":
            $ persistent._mas_pm_cares_island_progress = True
            $ mas_gainAffection(5, bypass=True)
            m 2hub "Ура!"

            call mas_islands(force_exp="monika 1hua")

            m "Надеюсь, тебе понравилось~"
            m 1lusdlb "Я знаю, что до завершения еще далеко, {w=0.2}{nw}"
            extend 1eka "но я очень хотела показать тебе свой прогресс."
            m 2lsp "Я всё ещё учусь кодировать, и непоследовательность этого движка мне не помогает..."
            m 7hub "Но я думаю, что на данный момент я добился немалого прогресса!"
            $ mas_setEventPause(10)
            $ mas_moni_idle_disp.force_by_code("1hua", duration=10, skip_dissolve=True)

        "Мне это неинтересно.":
            $ persistent._mas_pm_cares_island_progress = False
            $ mas_loseAffectionFraction(min_amount=50, modifier=1.0)
            m 2ekc "Ох..."
            m 6rktpc "Я..."
            m 6fktpd "Я очень много работала над этим..."
            m 2rktdc "Ты...{w=0.5} Ты, наверное, просто занят..."
            $ mas_setEventPause(60*10)
            $ mas_moni_idle_disp.force_by_code("2ekc", duration=60*10, skip_dissolve=True)

        "Может быть, позже.":
            m 2ekc "Ох...{w=0.5}{nw}"
            extend 2eka "хорошо."
            m 7eka "Только не заставляй меня ждать слишком долго~"
            $ mas_setEventPause(20)
            $ mas_moni_idle_disp.force_by_code("1euc", duration=20, skip_dissolve=True)

    return

# default persistent._mas_pm_likes_islands = None

# init 5 python:
#     addEvent(
#         Event(
#             persistent.event_database,
#             eventlabel="mas_monika_islands_final_reveal"
#         ),
#         restartBlacklist=True
#     )

# label mas_monika_islands_final_reveal:
#     python:
#         renpy.dynamic("islands_disp")
#         mas_island_event._final_unlocks()
#         islands_disp = mas_island_event.get_islands_displayable(False, False)

#     m 4sub "I'm so excited to finally show you my work!"

#     if mas_getCurrentBackgroundId() != "spaceroom":
#         m 7eua "Let's return to the classroom for the best view."
#         call mas_background_change(mas_background_def, skip_leadin=True, skip_outro=True)

#     m 1eua "Now let me turn off the light.{w=0.3}.{w=0.3}.{w=0.3}{nw}"

#     window hide
#     call .islands_scene
#     window auto

#     m "..."
#     m "I'm surprised it actually worked, ahaha!~"
#     m "You know, after spending so much time working on this..."
#     m "It feels so satisfying not only being able to see the result myself..."
#     m "But also being able to show it to you, [mas_get_player_nickname()]."
#     m "I'm sure you had been wondering what was behind that bug on the central island~"
#     m "It's a small house for us to spend time in, we can go there any time now, just ask."

#     if mas_background.getUnlockedBGCount() == 1:
#         m "I know staying in this empty classroom can feel tiresome sometimes."
#         m "So it's nice to get more places to visit."

#     else:
#         m "Even with all the other places we have, it's always nice to get new surroundings."

#     m "Now, why don't we go inside, [player]?"

#     window hide
#     call .zoom_in
#     window auto

#     python hide:
#         bg = mas_getBackground(mas_island_event.LIVING_ROOM_ID)
#         if bg:
#             mas_changeBackground(bg)
#         mas_island_event.stop_music()

#     call spaceroom(scene_change=True, dissolve_all=True, force_exp="monika 4hub")

#     m "Tada!~"
#     m 2eua "So, [player]..."
#     m 3eka "Your opinion is {i}really{/i} important to me."

#     call .ask_opinion

#     return

# label mas_monika_islands_final_reveal.islands_scene:
#     $ mas_RaiseShield_core()
#     $ mas_OVLHide()
#     $ mas_hotkeys.no_window_hiding = True
#     $ mas_play_song(None)
#     scene black with dissolve

#     $ mas_island_event.play_music()

#     # I'd love to split the lines properly, but renpy doesn't allow that, so have this cursed thing instead
#     show expression islands_disp as islands_disp at mas_islands_final_reveal_trans_1(
#         delay=mas_island_event.REVEAL_ANIM_DELAY,
#         move_time=mas_island_event.REVEAL_ANIM_1_DURATION - mas_island_event.REVEAL_ANIM_DELAY
#     ) zorder mas_island_event.DEF_SCREEN_ZORDER with mas_island_event.REVEAL_FADE_TRANSITION
#     $ renpy.pause(mas_island_event.REVEAL_ANIM_1_DURATION - mas_island_event.REVEAL_TRANSITION_TIME - mas_island_event.REVEAL_FADEIN_TIME, hard=True)

#     show expression islands_disp as islands_disp at mas_islands_final_reveal_trans_2(
#         delay=mas_island_event.REVEAL_ANIM_DELAY,
#         move_time=mas_island_event.REVEAL_ANIM_2_DURATION - mas_island_event.REVEAL_ANIM_DELAY
#     ) zorder mas_island_event.DEF_SCREEN_ZORDER with mas_island_event.REVEAL_FADE_TRANSITION
#     $ renpy.pause(mas_island_event.REVEAL_ANIM_2_DURATION - mas_island_event.REVEAL_TRANSITION_TIME - mas_island_event.REVEAL_FADEIN_TIME, hard=True)

#     show expression islands_disp as islands_disp at mas_islands_final_reveal_trans_3(
#         delay=mas_island_event.REVEAL_ANIM_DELAY,
#         move_time=mas_island_event.REVEAL_ANIM_3_1_DURATION - mas_island_event.REVEAL_ANIM_DELAY,
#         zoom_time=mas_island_event.REVEAL_ANIM_3_2_DURATION
#     ) zorder mas_island_event.DEF_SCREEN_ZORDER with mas_island_event.REVEAL_FADE_TRANSITION
#     $ renpy.pause(mas_island_event.REVEAL_ANIM_3_1_DURATION + mas_island_event.REVEAL_ANIM_3_2_DURATION - mas_island_event.REVEAL_TRANSITION_TIME, hard=True)

#     $ renpy.pause(mas_island_event.REVEAL_OVERVIEW_DURATION, hard=True)
#     $ mas_hotkeys.no_window_hiding = False
#     $ mas_OVLShow()
#     $ mas_DropShield_core()
#     $ mas_RaiseShield_dlg()

#     return

# label mas_monika_islands_final_reveal.zoom_in:
#     show expression islands_disp as islands_disp at mas_islands_final_reveal_trans_4(
#         delay=0.0,
#         zoom_time=mas_island_event.REVEAL_ANIM_4_DURATION
#     ) zorder mas_island_event.DEF_SCREEN_ZORDER
#     $ renpy.pause(mas_island_event.REVEAL_ANIM_4_DURATION - mas_island_event.REVEAL_FADEOUT_TIME, hard=True)
#     scene black with mas_island_event.REVEAL_DISSOLVE_TRANSITION

#     return

# label mas_monika_islands_final_reveal.ask_opinion:
#     m 1eksdla "What do you think?~{nw}"
#     $ _history_list.pop()
#     menu:
#         m "What do you think?~{fast}"

#         "It's not too bad.":
#             $ persistent._mas_pm_likes_islands = False
#             $ mas_loseAffectionFraction(min_amount=50, modifier=1.0)
#             $ mas_lockEVL("mas_monika_islands", "EVE")
#             m 2ekd "Oh...{w=0.3}{nw}"
#             extend 2lkc "I guess it's not perfect..."
#             m 2dktpc "But after all that time I've spent working for a place for us, {w=0.1}{nw}"
#             extend 2fktud "you could at least pretend to care."

#             if persistent._mas_pm_cares_island_progress is False:
#                 $ mas_loseAffectionFraction(min_amount=50, modifier=0.5)
#                 m 2dktsc "..."
#                 m 2gftpc "Although, what did I expect...{w=0.3}{nw}"
#                 extend 2eftud "you have said you don't care before."
#                 m 2dstdc "Forget, {w=0.3}{nw}"
#                 extend 2mstdc "this was a waste of time. {w=0.3}{nw}"
#                 extend 2tsc "For both of us."

#             else:
#                 m 2dktsc "It hurts, [player]... {w=0.3}It really, {w=0.1}{i}really{/i} hurts."
#                 m 2fftdd "You know what? {w=0.1}Forget. {w=0.3}{nw}"
#                 extend 2mftdc "It was a mistake from the start."

#             # TODO: reference monika_sweatercurse?

#         "You did an amazing job!":
#             $ persistent._mas_pm_likes_islands = True
#             $ mas_gainAffection(10, bypass=True)
#             m 1wuo "Really? {w=0.3}{nw}"
#             extend 2suo "You can't imagine how much that means to me, [player]!"
#             m 2fktpa "I'm so, {w=0.1}{i}so{/i} glad you liked it."

#             if persistent._mas_pm_cares_island_progress is False:
#                 $ mas_gainAffection(5, bypass=True)
#                 m 3rktdc "You've got me a bit worried before when you said you don't care about our islands..."
#                 m 1eka "It makes me incredibly happy you've changed your mind."

#             elif persistent._mas_pm_cares_island_progress:
#                 $ mas_gainAffection(5, bypass=True)
#                 m 3fktda "It's only because of your everlasting love and support I was able to finish this."

#             m 3hublb "Thanks for being my inspiration, [mas_get_player_nickname()]~"

#     return


label mas_islands(
    fade_in=True,
    fade_out=True,
    raise_shields=True,
    drop_shields=True,
    enable_interaction=True,
    check_progression=False,
    **spaceroom_kwargs
):
    # Sanity check
    if persistent._mas_islands_start_lvl is None or not mas_canShowIslands(False):
        return

    python:
        # NOTE: We can't progress filter here, it looks bad
        spaceroom_kwargs.setdefault("progress_filter", False)
        # Always scene change unless asked not to
        spaceroom_kwargs.setdefault("scene_change", True)
        is_done = False
        islands_displayable = mas_island_event.get_islands_displayable(
            enable_interaction=enable_interaction,
            check_progression=check_progression
        )
        renpy.start_predict(islands_displayable)

    if fade_in:
        # HACK: Show the disp so we can fade in
        # fix it in r7 where you can show/call screens with transitions
        scene
        show expression islands_displayable as islands_background onlayer screens zorder mas_island_event.DEF_SCREEN_ZORDER
        with Fade(0.5, 0, 0.5)
        hide islands_background onlayer screens with None

    if raise_shields:
        python:
            mas_OVLHide()
            mas_RaiseShield_core()
            disable_esc()
            mas_hotkeys.no_window_hiding = True

    if enable_interaction:
        # If this is an interaction, we call the screen so
        # the user can see the parallax effect + events
        while not is_done:
            hide screen mas_islands
            call screen mas_islands(islands_displayable)
            show screen mas_islands(islands_displayable, show_return_button=False)

            if _return is False:
                $ is_done = True

            elif _return is not True and renpy.has_label(_return):
                call expression _return

    else:
        # Otherwise just show it as a static image
        show screen mas_islands(islands_displayable, show_return_button=False)

    if drop_shields:
        python:
            mas_hotkeys.no_window_hiding = False
            enable_esc()
            mas_MUINDropShield()
            mas_OVLShow()

    if fade_out:
        hide screen mas_islands
        # HACK: Show the disp so we can fade out of it into spaceroom,
        # fix it in r7 where you can hide screens with transitions
        show expression islands_displayable as islands_background onlayer screens zorder mas_island_event.DEF_SCREEN_ZORDER with None
        call spaceroom(**spaceroom_kwargs)
        hide islands_background onlayer screens
        with Fade(0.5, 0, 0.5)

    python:
        renpy.stop_predict(islands_displayable)
        del islands_displayable, is_done
    return


label mas_island_upsidedownisland:
    if persistent._mas_o31_in_o31_mode and random.random() < 0.3:
        jump mas_island_spooky_ambience

    m "Ох, это."
    m "Думаю, тебе интересно, почему этот остров перевернут, верно?"
    m "Ну... я собиралась его починить, пока не посмотрела на него ещё раз внимательно."
    m "Это выглядит сюрреалистично, не так ли?"
    m "Я просто чувствую, что в этом есть что-то особенное."
    m "Это просто... завораживает."
    return

label mas_island_glitchedmess:
    m "Ох, это."
    m "Это то, над чем я сейчас работаю."
    m "Это все еще огромный беспорядок, хотя. Я всё ещё пытаюсь разобраться во всем этом."
    m "В своё время, я уверена, я стану лучше в кодировании!"
    m "Практика делает совершенным, в конце концов, верно?"
    return

label mas_island_cherry_blossom_tree:
    python:

        if not renpy.store.seen_event("mas_island_cherry_blossom1"):

            renpy.call("mas_island_cherry_blossom1")

        else:
            _mas_cherry_blossom_events = [
                "mas_island_cherry_blossom1",
                "mas_island_cherry_blossom3",
                "mas_island_cherry_blossom4"
            ]

            if not mas_island_event.is_winter_weather():
                _mas_cherry_blossom_events.append("mas_island_cherry_blossom2")

            renpy.call(renpy.random.choice(_mas_cherry_blossom_events))

    return

label mas_island_cherry_blossom1:
    if mas_island_event.is_winter_weather():
        m "Сейчас это дерево может выглядеть мертвым... но когда оно цветет, оно великолепно."

    else:
        m "Это красивое дерево, не так ли?"

    m "Это дерево называется цветущей сакурой; они родом из Японии."
    m "Традиционно, когда цветы распускаются, люди идут смотреть на цветы и устраивают пикник под деревьями."
    m "Ну, я выбрала это дерево не из-за традиции."
    m "Я выбрала его, потому что оно красивое и на него приятно смотреть."
    m "Просто смотреть на опадающие лепестки - это внушает благоговение."

    if mas_island_event.is_winter_weather():
        m "Когда она цветёт, то есть."
        m "Не могу дождаться, когда у нас появится возможность испытать это, [player]."

    return

label mas_island_cherry_blossom2:
    m "Знаешь ли ты, что можно есть лепестки цветов цветущей вишни?"
    m "Я сама не знаю вкуса, но уверена, что он не может быть таким сладким, как ты."
    m "Э-хе-хе~"
    return

label mas_island_cherry_blossom3:
    m "Знаешь, дерево символично, как сама жизнь."
    m "Красивое, но недолговечное."
    m "Но когда ты здесь, оно всегда прекрасно цветёт."

    if mas_island_event.is_winter_weather():
        m "Даже если сейчас она голая, скоро она снова расцветет."

    m "Знай, что я всегда буду благодарна тебе за то, что ты есть в моей жизни."
    m "Я люблю тебя, [player]~"
    # manually handle the "love" return key
    $ mas_ILY()
    return

label mas_island_cherry_blossom4:
    m "Знаешь, что было бы неплохо выпить под цветущей сакурой?"
    m "Немного сакэ~"
    m "А-ха-ха! Я просто шучу."
    m "Я бы лучше выпила чай или кофе."

    if mas_island_event.is_winter_weather():
        m "Или даже горячий шоколад. Это бы точно помогло справиться с холодом."
        m "Конечно, даже если это не поможет, мы всегда можем обниматься вместе...{w=0.5} Это было бы очень романтично~"

    else:
        m "Но было бы здорово смотреть на падающие лепестки вместе с тобой."
        m "Это было бы очень романтично~"

    return

label mas_island_sky:
    python:

        if mas_current_background.isFltDay():
            _mas_sky_events = [
                "mas_island_day1",
                "mas_island_day2",
                "mas_island_day3"
            ]

        else:
            _mas_sky_events = [
                "mas_island_night1",
                "mas_island_night2",
                "mas_island_night3"
            ]

        _mas_sky_events.append("mas_island_daynight1")
        _mas_sky_events.append("mas_island_daynight2")

        renpy.call(renpy.random.choice(_mas_sky_events))

    return

label mas_island_day1:
    #NOTE: this ordering is key, during winter we only use snow covered islands with clear sky
    # so Winter path needs to be first
    if mas_island_event.is_winter_weather():
        m "Какой прекрасный день сегодня."
        m "Идеально для прогулки, чтобы полюбоваться пейзажами."
        m "...прижавшись друг к другу, чтобы уберечься от холода."
        m "...С хорошими горячими напитками, чтобы согреться."

    elif mas_is_raining:
        m "Ах, я бы хотела почитать на свежем воздухе."
        m "Но я бы предпочла избежать намокания моих книг..."
        m "Мокрые страницы - это боль, с которой приходится иметь дело."
        m "Может быть, в другой раз."

    elif mas_current_weather == mas_weather_overcast:
        m "итать на улице при такой погоде было бы не так уж плохо, но дождь может пойти в любой момент."
        m "Я бы лучше не рисковала."
        m "Не волнуйся, [player]. Мы сделаем это в другой раз."

    else:
        m "Сегодня хороший день."

        if mas_island_event._is_unlocked("decal_tree"):
            m "Такая погода подойдет для чтения книги под цветущей сакурой, верно, [player]?"

        else:
            m "Такая погода подходит для чтения книги на улице, верно, [player]?"

        m "Лежа в тени за чтением моей любимой книги."
        m "...Вместе с закуской и любимым напитком на гарнир."
        m "Ах-х, это было бы очень приятно сделать~"

    return

label mas_island_day2:
    #NOTE: this ordering is key, during winter we only use snow covered islands with clear sky
    # so Winter path needs to be first
    if mas_island_event.is_winter_weather():
        m "Ты когда-нибудь делал снежного ангела, [player]?"
        m "Я пыталась в прошлом, но никогда не имела особого успеха..."
        m "Это намного сложнее, чем кажется."
        m "Уверена, мы получим массу удовольствия, даже если то, что мы сделаем, не будет похоже на ангела."
        m "Просто нужно быть немного глупым, понимаешь?"

    elif mas_island_event.is_cloudy_weather():
        m "Выходить на улицу в такую погоду выглядит не очень привлекательно..."
        m "Может быть, если бы у меня был зонтик, я бы чувствовала себя более комфортно."
        m "Представь нас обоих, защищенных от дождя, на расстоянии дюйма друг от друга."
        m "Смотрим друг другу в глаза."
        m "Затем мы начинаем наклоняться все ближе и ближе, пока не окажемся почти-"
        m " думаю, ты можешь закончить эту мысль сам, [player]~"

    else:
        m "Погода выглядит хорошо."
        m "Это определенно лучшее время для пикника."
        m "У нас даже есть прекрасный вид, чтобы его провести!"
        m "Разве это не здорово?"

        if mas_island_event._is_unlocked("decal_tree"):
            m "Едим под цветущим деревом сакуры."

        m "Любуемся окружающими пейзажами."
        m "Наслаждаясь компанией друг друга."
        m "Ах, это было бы фантастично~"

    return

label mas_island_day3:
    if mas_is_raining and not mas_isWinter():
        m "Идет сильный дождь..."
        m "Я бы не хотела сейчас находиться на улице."
        m "Хотя находиться в помещении в такое время довольно уютно, не находишь?"

    else:
        m "На улице довольно спокойно."

        if mas_island_event.is_winter_weather():
            m "Мы могли бы устроить бой снежками, знаешь ли."
            m "А-ха-ха, это было бы так весело!"
            m "Спорим, я смогу попасть в тебя с расстояния в несколько островов."
            m "Немного здоровой соревновательности никогда никому не повредит, верно?"

        else:
            m "Я бы не отказалась поваляться в траве прямо сейчас..."
            m "С твоей головой на моих коленях..."
            m "Э-хе-хе~"

    return

label mas_island_night1:
    m "Хотя днем приятно быть продуктивным, в ночи есть что-то такое умиротворяющее."
    m "Звуки стрекотания сверчков в сочетании с легким бризом так расслабляют."
    m "Ты бы обнял меня в такую ночь, так ведь~"
    return

label mas_island_night2:
    if not mas_isWinter() and mas_island_event.is_cloudy_weather():
        m "Жаль, что сегодня вечером мы не сможем увидеть звезды..."
        m "Я бы с удовольствием полюбовалась космосом вместе с тобой."
        m "Ничего страшного, мы сможем увидеть это в другой раз."

    else:
        if seen_event('monika_stargazing'):
            m "Разве звёзды не так прекрасны, [player]?"
            m "Хотя, это не {i}совсем{/i} то, что я имела в виду, когда говорила о наблюдении за звездами..."
            m "Как бы ни было приятно на них смотреть, больше всего я хочу испытать это с тобой, крепко обнимая друг друга, пока мы лежим там."
            m "Когда-нибудь, [player].{w=0.3} Когда-нибудь."

        else:
            m "Ты когда-нибудь ходил смотреть на звезды, [mas_get_player_nickname()]?"
            m "Выделить немного времени из своего вечера, чтобы посмотреть на ночное небо и просто поглазеть на красоту неба над головой..."
            m "Это удивительно расслабляет, понимаешь?"
            m "Я обнаружила, что это действительно может снять стресс и очистить голову..."
            m "А вид всевозможных созвездий на небе просто наполняет твой разум удивлением."
            m "Конечно, это действительно заставляет понять, насколько мы малы во Вселенной."
            m "А-ха-ха..."

    return

label mas_island_night3:
    if not mas_isWinter() and mas_island_event.is_cloudy_weather():
        m "Облачная погода немного угнетает, не находишь?"
        m "Особенно ночью, когда она скрывает звезды от нашего взгляда."
        m "Это такая жалость, правда..."

    else:
        m "Какая прекрасная ночь!"

        if mas_island_event.is_winter_weather():
            m "Просто есть что-то в холодной, хрустящей ночи, что я люблю."
            m "Контраст темного неба и земли, покрытой снегом, действительно захватывает дух, не так ли?"
        else:
            m "Если бы я могла, я бы добавила светлячков."
            m "Их свет дополняет ночное небо, это красивое зрелище."
            m "Немного улучшить атмосферу, как ты думаешь?"

    return

label mas_island_daynight1:
    m "Может быть, мне стоит добавить больше кустов и деревьев."
    m "Сделать острова красивее, понимаешь?"
    m "Мне просто нужно найти подходящие цветы и листву."
    m "А может, на каждом острове должен быть свой набор растений, чтобы все было по-разному и разнообразно."
    m "Я начинаю волноваться, думая об этом~"
    return

label mas_island_daynight2:
    # aurora borealis
    m "{i}~Ветряная мельница, ветряная мельница для земли~{/i}"

    # a-aurora borealis
    m "{i}~Повернуть навсегда рука об руку~{/i}"

    # aurora borealis
    m "{i}~Принять все это как должное~{/i}"

    # at this time of day?
    m "{i}~Тикает, падает~{/i}"

    # aurora borealis
    m "{i}~Любовь вечна, любовь свободна~{/i}"

    # a-aurora borealis
    m "{i}~Давай навеки, ты и я~{/i}"

    # in this part of the country? Yes
    m "{i}~Ветряная мельница, ветряная мельница для земли~{/i}"

    m "Э-хе-хе, не обращай внимания, просто захотелось спеть от души~"
    return

label mas_island_shimeji:
    m "Ах!"
    m "Как она туда попала?"
    m "Дай мне секунду, [player].{w=0.2}.{w=0.2}.{w=0.2}{nw}"
    $ islands_displayable.remove(mas_island_event.other_disp_map["other_shimeji"])
    m "Всё готово!"
    m "Не волнуйся, я просто переместила её в другое место."
    return

label mas_island_bookshelf:
    python:

        _mas_bookshelf_events = [
            "mas_island_bookshelf1",
            "mas_island_bookshelf2"
        ]

        renpy.call(renpy.random.choice(_mas_bookshelf_events))

    return

label mas_island_bookshelf1:
    #NOTE: this ordering is key, during winter we only use snow covered islands with clear sky
    # so Winter path needs to be first
    if mas_island_event.is_winter_weather():
        m "Эта книжная полка может выглядеть не очень прочной, но я уверена, что она выдержит небольшой снегопад."
        m "Меня немного беспокоят книги."
        m "Я просто надеюсь, что они не слишком пострадают..."

    elif mas_island_event.is_cloudy_weather():
        m "В такие моменты я жалею, что не держу свои книги в помещении..."
        m "Похоже, нам придется подождать лучшей погоды, чтобы почитать их."
        m "А пока..."
        m "Как насчет того, чтобы немного пообниматься, [player]?"
        m "Э-хе-хе~"

    else:
        m "Там некоторые из моих любимых книг."
        m "{i}451 градус по Фаренгейту{/i}, {i}Страна чудес в твердом переплете{/i}, {i}Девятнадцать восемьдесят четыре{/i}, и многие другие."
        m "Может быть, мы когда-нибудь прочитаем их вместе~"

    return

label mas_island_bookshelf2:
    #NOTE: this ordering is key, during winter we only use snow covered islands with clear sky
    # so Winter path needs to be first
    if mas_island_event.is_winter_weather():
        m "Знаешь, я не против почитать на улице, даже если выпадет немного снега."
        m "Хотя я бы не решилась выйти на улицу без теплого пальто, толстого шарфа и удобных перчаток."
        m "Думаю, в таком случае перелистывать страницы будет трудновато, а-ха-ха..."
        m "Но я уверена, что мы как-нибудь справимся."
        m "Не так ли, [player]?"

    elif mas_island_event.is_cloudy_weather():
        m "Читать в помещении, когда за окном льет дождь, довольно расслабляюще."
        m "Если бы только я не оставила книги на улице..."
        m "Наверное, мне стоит принести их сюда, когда представится возможность."
        m "Я уверена, что мы сможем найти другие занятия на это время, верно [player]?"

    else:
        m "Чтение на свежем воздухе - хорошая смена темпа, знаешь?"
        m "Я бы в любой день предпочла прохладный ветерок душной библиотеке."
        m "Может быть, мне стоит поставить столик под цветущим деревом."
        m "Было бы здорово выпить чашечку кофе с закусками и почитать книгу."
        m "Это было бы замечательно~"

    return

label mas_island_distant_islands:
    if persistent._mas_o31_in_o31_mode:
        jump mas_island_spooky_ambience

    return

label mas_island_spooky_ambience:
    m "{i}Это была темная и бурная ночь...{/i}"
    m "Э-хе-хе~ Это идеальное время года для жутких историй, не так ли?"
    m "Если ты в настроении, мы должны почитать несколько вместе."
    m "Хотя, я не против пока просто наслаждаться атмосферой вместе с тобой."

    return

label mas_island_bloodfall:
    m "Я очень горжусь этим водопадом. Он уже выглядел довольно сюрреалистично, будучи перевернутым."
    m "Все, что мне действительно нужно было сделать, это изменить значение воды на #641F21, и--{nw}"
    $ _history_list.pop()
    m "Подожди, я не хочу разрушать волшебство для тебя!{w=0.2} Забудь, что я это сказал, пожалуйста!"

    return

label mas_island_pumpkins:
    m "Ничто не напоминает мне о Хэллоуине так сильно, как тыквы."
    m "Я подумала, что будет так уютно, если вокруг моего уголка для чтения их будет много."
    m "Немного прохладно под дождем, но не думаешь ли ты, что было бы здорово надеть свитера и прижаться друг к другу?"
    m "Может быть, я могла бы сварить ароматный кофе, чтобы еще больше улучшить настроение."

    return

label mas_island_gravestones:
    if mas_safeToRefDokis():
        m "Что?"
        m "...{w=0.2}}Какие надгробия? {w=0.2}Я не понимаю, о чем ты говоришь."
        m "Ты...{w=0.2}пффф--"
        m "А-ха-ха!"
        m "Прости, не смогла удержаться."
        m "Было бы довольно жутко, если бы эти трое всё ещё преследовали наш счастливый конец, не так ли?"

    else:
        m "Э-хе-хе... я не уверена, что эти украшения подходят по вкусу."
        m "Я тут подумала...{w=0.2}Хэллоуин - это время, когда в некоторых культурах чествуют мертвых."
        m "Конечно, есть много жутких историй о восставших мертвецах или призраках, преследующих людей..."
        m "Но есть и такая сторона этого праздника, как память, не так ли?"
        m "Наверное, я просто подумала, что не стоит оставлять их без внимания."

    return


# TODO: Allow to hide ui with H and mouse 2 clicks w/o globals
screen mas_islands(islands_displayable, show_return_button=True):
    style_prefix "island"
    layer "screens"
    zorder mas_island_event.DEF_SCREEN_ZORDER

    if show_return_button:
        key "K_ESCAPE" action Return(False)

    add islands_displayable

    if show_return_button:
        # Unsure why, but w/o a hbox renpy won't apply the style prefix
        hbox:
            align (0.5, 0.98)
            textbutton _("Вернуться"):
                action Return(False)

# screen mas_islands_background:

#     add mas_island_event.getBackground()

#     if _mas_island_shimeji:
#         add "gui/poemgame/m_sticker_1.png" at moni_sticker_mid:
#             xpos 935
#             ypos 395
#             zoom 0.5

# screen mas_show_islands():
#     style_prefix "island"
#     imagemap:

#         ground mas_island_event.getBackground()

#         hotspot (11, 13, 314, 270) action Return("mas_island_upsidedownisland") # island upside down
#         hotspot (403, 7, 868, 158) action Return("mas_island_sky") # sky
#         hotspot (699, 347, 170, 163) action Return("mas_island_glitchedmess") # glitched house
#         hotspot (622, 269, 360, 78) action Return("mas_island_cherry_blossom_tree") # cherry blossom tree
#         hotspot (716, 164, 205, 105) action Return("mas_island_cherry_blossom_tree") # cherry blossom tree
#         hotspot (872, 444, 50, 30) action Return("mas_island_bookshelf") # bookshelf

#         if _mas_island_shimeji:
#             hotspot (935, 395, 30, 80) action Return("mas_island_shimeji") # Mini Moni

#     if _mas_island_shimeji:
#         add "gui/poemgame/m_sticker_1.png" at moni_sticker_mid:
#             xpos 935
#             ypos 395
#             zoom 0.5

#     hbox:
#         yalign 0.98
#         xalign 0.96
#         textbutton _mas_toggle_frame_text action [ToggleVariable("_mas_island_window_open"),ToggleVariable("_mas_toggle_frame_text","Open Window", "Close Window") ]
#         textbutton "Go Back" action Return(False)


# Defining a new style for buttons, because other styles look ugly

# properties for these island view buttons
style island_button is generic_button_light:
    xysize (205, None)
    ypadding 5
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style island_button_dark is generic_button_dark:
    xysize (205, None)
    ypadding 5
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style island_button_text is generic_button_text_light:
    font gui.default_font
    size gui.text_size
    xalign 0.5
    kerning 0.2
    outlines []

style island_button_text_dark is generic_button_text_dark:
    font gui.default_font
    size gui.text_size
    xalign 0.5
    kerning 0.2
    outlines []

# mini moni ATL
# transform moni_sticker_mid:
#     block:
#         function randomPauseMonika
#         parallel:
#             sticker_move_n
#         repeat
