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
default persistent._mas_islands_unlocks = store.mas_island_event.IslandsImageDefinition.getDefaultUnlocks()


### initialize the island images
init 1:
    #   if for some reason we fail to convert the files into images
    #   then we must backout of showing the event.
    #
    #   NOTE: other things to note:
    #       on o31, we cannot have islands event
    define mas_decoded_islands = store.mas_island_event.decodeImages()
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

# # # Image defination
init -20 python in mas_island_event:
    class IslandsImageDefinition(object):
        """
        A generalised abstraction around raw data for the islands sprites
        """
        TYPE_ISLAND = "island"
        TYPE_DECAL = "decal"
        TYPE_BG = "bg"
        TYPE_OVERLAY = "overlay"
        TYPE_OBJECT = "obj"# This is basically for everything else
        TYPES = frozenset(
            (
                TYPE_ISLAND,
                TYPE_DECAL,
                TYPE_BG,
                TYPE_OVERLAY,
                TYPE_OBJECT
            )
        )

        DELIM = "_"

        _data_map = dict()

        def __init__(
            self,
            id_,
            type_=None,
            default_unlocked=False,
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
                        - 'obj_###'
                        where ### is something unique
                type_ - type of this sprite, if None, we automatically get it from the id
                    (Default: None)
                default_unlocked - whether or not this sprite is unlocked from the get go
                    (Default: False)
                fp_map - the map of the images for this sprite, if None, we automatically generate it
                    NOTE: after decoding this will point to a loaded ImageData object instead of a failepath
                    (Default: None)
                partial_disp - functools.partial of the displayable for this sprite
                    (Default: None)
            """
            if id_.split(self.DELIM)[0] not in self.TYPES:
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
            self.fp_map = fp_map if fp_map is not None else self._buildFPMap()
            self.partial_disp = partial_disp

            self._data_map[id_] = self

        def _getType(self):
            """
            Private method to get type of this sprite if it hasn't been passed in

            OUT:
                str
            """
            return self.id.split(self.DELIM)[0]

        def _buildFPMap(self):
            """
            Private method to build filepath map if one hasn't been passed in

            OUT:
                dict
            """
            filepath_fmt = "{prefix}s/{name}/{suffix}"
            prefix, name = self.id.split(self.DELIM)
            # Otherlays are a bit different
            if self.type == self.TYPE_OVERLAY:
                suffixes = ("d", "n")

            else:
                suffixes = ("d", "d_r", "d_s", "n", "n_r", "n_s", "s", "s_r", "s_s")

            # FIXME: Use f-strings with py3 pls
            return {
                suffix: filepath_fmt.format(
                    prefix=prefix,
                    name=name,
                    suffix=suffix
                )
                for suffix in suffixes
            }

        @classmethod
        def getDataFor(cls, id_):
            """
            Returns data for an id

            OUT:
                IslandsImageDefinition
            """
            return cls._data_map[id_]

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
    IslandsImageDefinition(
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
    IslandsImageDefinition(
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
    IslandsImageDefinition(
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
    IslandsImageDefinition(
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
    IslandsImageDefinition(
        "island_4",
        partial_disp=functools.partial(
            ParallaxSprite,
            x=-15,
            y=-15,
            z=125,
            on_click="mas_island_upsidedownisland"
        )
    )
    IslandsImageDefinition(
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
    IslandsImageDefinition(
        "island_6",
        partial_disp=functools.partial(
            ParallaxSprite,
            x=912,
            y=46,
            z=200,
            function=None,
            on_click=True
        )
    )
    IslandsImageDefinition(
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
    IslandsImageDefinition(
        "island_8",
        partial_disp=functools.partial(
            ParallaxSprite,
            x=484,
            y=54,
            z=220,
            on_click=True
        )
    )
    # Decals
    IslandsImageDefinition(
        "decal_bookshelf",
        partial_disp=functools.partial(
            ParallaxDecal,
            x=358,
            y=55,
            z=4,
            on_click="mas_island_bookshelf"
        )
    )
    IslandsImageDefinition(
        "decal_bushes",
        partial_disp=functools.partial(
            ParallaxDecal,
            x=305,
            y=63,
            z=5,
            on_click=True
        )
    )
    IslandsImageDefinition(
        "decal_house",
        partial_disp=functools.partial(
            ParallaxDecal,
            x=215,
            y=-44,
            z=1
        )
    )
    IslandsImageDefinition(
        "decal_tree",
        partial_disp=functools.partial(
            ParallaxDecal,
            x=130,
            y=-200,
            z=3,
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
    IslandsImageDefinition(
        "decal_glitch",
        fp_map={},
        partial_disp=functools.partial(
            ParallaxDecal,
            x=216,
            y=-54,
            z=2,
            on_click="mas_island_glitchedmess"
        )
    )
    IslandsImageDefinition(
        "obj_shimeji",
        fp_map={},
        partial_disp=functools.partial(
            ParallaxSprite,
            Transform(renpy.easy.displayable("chibika smile"), zoom=0.4),
            x=930,
            y=335,
            z=36,
            function=__chibi_transform_func,
            on_click="mas_island_shimeji"
        )
    )
    # BGs
    IslandsImageDefinition(
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
    IslandsImageDefinition(
        "overlay_rain",
        default_unlocked=True,
        partial_disp=functools.partial(
            MASFilterWeatherDisplayable,
            use_fb=True
        )
    )
    IslandsImageDefinition(
        "overlay_snow",
        default_unlocked=True,
        partial_disp=functools.partial(
            MASFilterWeatherDisplayable,
            use_fb=True
        )
    )
    IslandsImageDefinition(
        "overlay_thunder",
        default_unlocked=True,
        fp_map={},
        partial_disp=functools.partial(
            renpy.easy.displayable,
            "mas_islands_lightning_overlay"
        )
    )


# # # Main framework
init -25 python in mas_island_event:
    import random
    import functools
    import math
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
    # TODO: add a few more lvl
    MAX_PROGRESS_LOVE = 7
    PROGRESS_FACTOR = 4

    SHIMEJI_CHANCE = 100
    DEF_SCREEN_ZORDER = 55

    SUPPORTED_FILTERS = frozenset(
        {
            mas_sprites.FLT_DAY,
            mas_sprites.FLT_NIGHT,
            mas_sprites.FLT_SUNSET
        }
    )

    # These're being populated later once we decode the imgs
    island_disp_map = dict()
    decal_disp_map = dict()
    obj_disp_map = dict()
    bg_disp_map = dict()
    overlay_disp_map = dict()

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

    @mas_utils.deprecated()
    def shouldDecodeImages():
        """
        DEPRECATED
        A united check whether or not we should decode images in this sesh
        """
        return (
            not store.mas_isO31()
            # and (X or not Y)
        )

    def decodeImages():
        """
        Attempts to decode the images

        OUT:
            True upon success, False otherwise
        """
        err_msg = "[ERROR] Failed to decode images: {}.\n"

        pkg = islands_station.getPackage("our_reality")

        if not pkg:
            mas_utils.writelog(err_msg.format("Missing package"))
            return False

        pkg_data = islands_station.unpackPackage(pkg, pkg_slip=mas_ics.ISLAND_PKG_CHKSUM)

        if not pkg_data:
            mas_utils.writelog(err_msg.format("Bad package."))
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
            with ZipFile(pkg_data, "r") as zip_file:
                island_map = IslandsImageDefinition.getFilepathsForType(IslandsImageDefinition.TYPE_ISLAND)
                decal_map = IslandsImageDefinition.getFilepathsForType(IslandsImageDefinition.TYPE_DECAL)
                bg_map = IslandsImageDefinition.getFilepathsForType(IslandsImageDefinition.TYPE_BG)
                overlay_map = IslandsImageDefinition.getFilepathsForType(IslandsImageDefinition.TYPE_OVERLAY)
                # Now override maps to contain imgs instead of img paths
                for map_ in (island_map, decal_map, bg_map, overlay_map):
                    _read_zip(zip_file, map_)

                # Anim frames are handled a bit differently
                glitch_frames = tuple(
                    (store.MASImageData(zip_file.read(fn), fn + ".png") for fn in GLITCH_FPS)
                )

        except Exception as e:
            mas_utils.writelog(err_msg.format(e))
            return False

        else:
            # We loaded the images, now create dynamic displayables
            _buildDisplayables(island_map, decal_map, bg_map, overlay_map, glitch_frames)

        return True

    def _buildDisplayables(island_imgs_maps, decal_imgs_maps, bg_imgs_maps, overlay_imgs_maps, glitch_frames):
        """
        Takes multiple maps with images and builds displayables from them, sets global vars
        NOTE: no sanity checks
        FIXME: py3 update

        IN:
            island_imgs_maps - the map from island names to raw images map
            decal_imgs_maps - the map from decal names to raw images map
            bg_imgs_maps - the map from bg ids to raw images map
            overlay_imgs_maps - the map from overlay ids to raw images map
            glitch_frames - tuple of glitch raw anim frames
        """
        global island_disp_map, decal_disp_map, obj_disp_map, bg_disp_map, overlay_disp_map

        # Build the islands
        for island_name, img_map in island_imgs_maps.iteritems():
            disp = IslandFilterWeatherDisplayable(
                day=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["d"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["d_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["d_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["d_r"]
                    }
                ),
                night=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["n"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["n_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["n_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["n_r"]
                    }
                ),
                sunset=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["s"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["s_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["s_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["s_r"]
                    }
                )
            )
            partial_disp = IslandsImageDefinition.getDataFor(island_name).partial_disp
            island_disp_map[island_name] = partial_disp(disp)

        # Build the decals
        for decal_name, img_map in decal_imgs_maps.iteritems():
            disp = IslandFilterWeatherDisplayable(
                day=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["d"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["d_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["d_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["d_r"]
                    }
                ),
                night=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["n"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["n_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["n_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["n_r"]
                    }
                ),
                sunset=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["s"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["s_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["s_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["s_r"]
                    }
                )
            )
            partial_disp = IslandsImageDefinition.getDataFor(decal_name).partial_disp
            decal_disp_map[decal_name] = partial_disp(disp)

        # Build the bg
        for bg_name, img_map in bg_imgs_maps.iteritems():
            disp = IslandFilterWeatherDisplayable(
                day=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["d"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["d_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["d_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["d_r"]
                    }
                ),
                night=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["n"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["n_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["n_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["n_r"]
                    }
                ),
                sunset=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["s"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["s_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["s_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["s_r"]
                    }
                )
            )
            partial_disp = IslandsImageDefinition.getDataFor(bg_name).partial_disp
            bg_disp_map[bg_name] = partial_disp(disp)

        # Build the overlays
        overlay_speed_map = {
            "overlay_rain": 0.8,
            "overlay_snow": 3.5
        }
        for overlay_name, img_map in overlay_imgs_maps.iteritems():
            # Overlays are just dynamic displayables
            partial_disp = IslandsImageDefinition.getDataFor(overlay_name).partial_disp
            overlay_disp_map[overlay_name] = store.mas_islands_weather_overlay_transform(
                child=partial_disp(
                    day=MASWeatherMap(
                        {
                            mas_weather.PRECIP_TYPE_DEF: img_map["d"]
                        }
                    ),
                    night=MASWeatherMap(
                        {
                            mas_weather.PRECIP_TYPE_DEF: img_map["n"]
                        }
                    ),
                    # sunset=MASWeatherMap(
                    #     {
                    #         mas_weather.PRECIP_TYPE_DEF: img_map["s"]
                    #     }
                    # )
                ),
                speed=overlay_speed_map.get(overlay_name, 1.0)
            )

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
        partial_disp = IslandsImageDefinition.getDataFor("decal_glitch").partial_disp
        decal_disp_map["decal_glitch"] = partial_disp(glitch_disp)

        # Build chibi disp
        partial_disp = IslandsImageDefinition.getDataFor("obj_shimeji").partial_disp
        obj_disp_map["obj_shimeji"] = partial_disp()

        # Build thunder overlay
        partial_disp = IslandsImageDefinition.getDataFor("overlay_thunder").partial_disp
        overlay_disp_map["overlay_thunder"] = partial_disp()

        return

    def _isUnlocked(id_):
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


    # # # START functions for lvl unlocks, head to __handleUnlocks to understand how this works
    # NOTE: Please, keep these private
    def __unlocks_for_lvl_0():
        _unlock("island_1")
        _unlock("island_8")

    def __unlocks_for_lvl_1():
        _unlock("obj_shimeji")
        _unlock("decal_glitch")

    def __unlocks_for_lvl_2():
        _unlock("island_2")

    def __unlocks_for_lvl_3():
        # Unlock only one, the rest at lvl 5
        if (
            not _isUnlocked("island_4")
            and not _isUnlocked("island_5")
        ):
            if bool(random.randint(0, 1)):
                _unlock("island_4")

            else:
                _unlock("island_5")

    def __unlocks_for_lvl_4():
        # Unlock only one, the rest at lvl 6
        if (
            not _isUnlocked("island_6")
            and not _isUnlocked("island_7")
        ):
            if bool(random.randint(0, 1)):
                _unlock("island_6")

            else:
                _unlock("island_7")

    def __unlocks_for_lvl_5():
        _unlock("decal_bushes")
        # Unlock everything from lvl 3
        _unlock("island_4")
        _unlock("island_5")

    def __unlocks_for_lvl_6():
        _unlock("island_3")
        # Unlock only one, the rest at lvl 7
        if (
            not _isUnlocked("decal_bookshelf")
            and not _isUnlocked("decal_tree")
        ):
            if bool(random.randint(0, 1)):
                _unlock("decal_bookshelf")

            else:
                _unlock("decal_tree")
        # Unlock everything from lvl 4
        _unlock("island_7")
        _unlock("island_6")

    def __unlocks_for_lvl_7():
        # Unlock everything from lvl 6
        _unlock("decal_bookshelf")
        _unlock("decal_tree")

    def __unlocks_for_lvl_8():
        # TODO: me
        # Also update monika_why_spaceroom
        return

    # # # END


    def __handleUnlocks():
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

    def _calcProgress(curr_lvl, start_lvl):
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
                modifier -= 0.1

            elif persistent._mas_pm_cares_island_progress is False:
                modifier += 0.2

            progress_factor = PROGRESS_FACTOR * modifier

            progress = min(int(lvl_difference / progress_factor), max_progress)

        else:
            progress = DEF_PROGRESS

        return progress

    def advanceProgression():
        """
        Increments the lvl of progression of the islands event,
        it will do nothing if the player hasn't unlocked the islands yet or if
        the current lvl is invalid
        """
        # If this var is None, then the user hasn't unlocked the event yet
        if persistent._mas_islands_start_lvl is None:
            return

        new_progress = _calcProgress(store.mas_xp.level(), persistent._mas_islands_start_lvl)

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
            and store.mas_timePastSince(store.mas_getEVL_last_seen("mas_monika_islands"), datetime.timedelta(days=3))
        ):
            store.MASEventList.push("mas_monika_islands_progress")

        # Now set new level
        persistent._mas_islands_progress = min(max(new_progress, curr_progress), MAX_PROGRESS_LOVE)
        # Run unlock callbacks
        __handleUnlocks()

        return

    def getProgression():
        """
        Returns current islands progress lvl
        """
        return persistent._mas_islands_progress

    def startProgression():
        """
        Starts islands progression
        """
        if store.mas_isMoniEnamored(higher=True) and persistent._mas_islands_start_lvl is None:
            persistent._mas_islands_start_lvl = store.mas_xp.level()
            advanceProgression()

    def _resetProgression():
        """
        Resets island progress
        """
        persistent._mas_islands_start_lvl = None
        persistent._mas_islands_progress = DEF_PROGRESS
        persistent._mas_islands_unlocks = IslandsImageDefinition.getDefaultUnlocks()

    def getIslandsDisplayable(enable_interaction=True, check_progression=False):
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

        def _reset_parallax_disp(disp):
            # Just in case we always remove all decals and readd them as needed
            disp.clear_decals()
            # Toggle events as desired
            disp.toggle_events(enable_interaction)
            # Reset offsets and zoom
            disp.reset_mouse_pos()
            disp.zoom = disp.min_zoom

        # Progress lvl
        if check_progression:
            advanceProgression()

        sub_displayables = list()

        # Add all unlocked islands
        for key, disp in island_disp_map.iteritems():
            if _isUnlocked(key):
                _reset_parallax_disp(disp)
                sub_displayables.append(disp)

        # Add all unlocked decals for islands 1 (other islands don't have any as of now)
        island_disp_map["island_1"].add_decals(
            *[
                decal_disp_map[key]
                for key in (
                    "decal_bookshelf",
                    "decal_bushes",
                    "decal_house",
                    "decal_tree",
                    "decal_glitch"
                )
                if _isUnlocked(key)
            ]
        )

        if _isUnlocked("obj_shimeji") and renpy.random.randint(1, SHIMEJI_CHANCE) == 1:
            shimeji_disp = obj_disp_map["obj_shimeji"]
            _reset_parallax_disp(shimeji_disp)
            SHIMEJI_CHANCE *= 2
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

        return ParallaxBackground(*sub_displayables)

    def isWinterWeather():
        """
        Checks if the weather on the islands is wintery

        OUT:
            boolean:
                - True if we're using snow islands
                - False otherwise
        """
        return store.mas_is_snowing or store.mas_isWinter()

    def isCloudyWeather():
        """
        Checks if the weather on the islands is cloudy

        OUT:
            boolean:
                - True if we're using overcast/rain islands
                - False otherwise
        """
        return store.mas_is_raining or store.mas_current_weather == store.mas_weather_overcast


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
            $ mas_gainAffection(3, bypass=True)
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
            $ mas_loseAffection(25)
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
        islands_displayable = mas_island_event.getIslandsDisplayable(
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

            if not mas_island_event.isWinterWeather():
                _mas_cherry_blossom_events.append("mas_island_cherry_blossom2")

            renpy.call(renpy.random.choice(_mas_cherry_blossom_events))

    return

label mas_island_cherry_blossom1:
    if mas_island_event.isWinterWeather():
        m "Сейчас это дерево может выглядеть мертвым... но когда оно цветет, оно великолепно."

    else:
        m "Это красивое дерево, не так ли?"

    m "Это дерево называется цветущей сакурой; они родом из Японии."
    m "Традиционно, когда цветы распускаются, люди идут смотреть на цветы и устраивают пикник под деревьями."
    m "Ну, я выбрала это дерево не из-за традиции."
    m "Я выбрала его, потому что оно красивое и на него приятно смотреть."
    m "Просто смотреть на опадающие лепестки - это внушает благоговение."

    if mas_island_event.isWinterWeather():
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

    if mas_island_event.isWinterWeather():
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

    if mas_island_event.isWinterWeather():
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
    if mas_island_event.isWinterWeather():
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

        if mas_island_event._isUnlocked("decal_tree"):
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
    if mas_island_event.isWinterWeather():
        m "Ты когда-нибудь делал снежного ангела, [player]?"
        m "Я пыталась в прошлом, но никогда не имела особого успеха..."
        m "Это намного сложнее, чем кажется."
        m "Уверена, мы получим массу удовольствия, даже если то, что мы сделаем, не будет похоже на ангела."
        m "Просто нужно быть немного глупым, понимаешь?"

    elif mas_island_event.isCloudyWeather():
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

        if mas_island_event._isUnlocked("decal_tree"):
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

        if mas_island_event.isWinterWeather():
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
    if not mas_isWinter() and mas_island_event.isCloudyWeather():
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
    if not mas_isWinter() and mas_island_event.isCloudyWeather():
        m "Облачная погода немного угнетает, не находишь?"
        m "Особенно ночью, когда она скрывает звезды от нашего взгляда."
        m "Это такая жалость, правда..."

    else:
        m "Какая прекрасная ночь!"

        if mas_island_event.isWinterWeather():
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
    $ islands_displayable.remove(mas_island_event.obj_disp_map["obj_shimeji"])
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
    if mas_island_event.isWinterWeather():
        m "Эта книжная полка может выглядеть не очень прочной, но я уверена, что она выдержит небольшой снегопад."
        m "Меня немного беспокоят книги."
        m "Я просто надеюсь, что они не слишком пострадают..."

    elif mas_island_event.isCloudyWeather():
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
    if mas_island_event.isWinterWeather():
        m "Знаешь, я не против почитать на улице, даже если выпадет немного снега."
        m "Хотя я бы не решилась выйти на улицу без теплого пальто, толстого шарфа и удобных перчаток."
        m "Думаю, в таком случае перелистывать страницы будет трудновато, а-ха-ха..."
        m "Но я уверена, что мы как-нибудь справимся."
        m "Не так ли, [player]?"

    elif mas_island_event.isCloudyWeather():
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
