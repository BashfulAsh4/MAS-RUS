# AFF010 is progpoints
#
# Affection module:
#
# General:
#
# This module is aimed to keep track and determine Monika's affection
# towards the player. Said affection level will be used to trigger
# specific events.
#
# Affection mechanics:
#
# - Affection gain has a 7 points cap per day
# - Affection lose doesn't have a cap
# - Max and Min possible values for affection are 1000000 and -1000000 respectively
# - Player lose affection every time it takes longer than 1 week to visit Monika
#     the reduction is measured by the formula number_of_days_absent * 0.5
#     if by doing that reduction affection were to be higher than -101 it will be
#     be set to -101. If absent time were higher than 10 years she'll go to -200
# - Affection is given or lost by specific actions the player can do or decisions
#     the player makes
#
# Affection level determine some "states" in which Monika is. Said states are the
# following:
#
# LOVE (1000 and up)
#   Monika is completely comfortable with the player.
#   (aka the comfortable stage in a relationship)
# ENAMORED (400 up to 999)
#     Exceptionally happy, the happiest she has ever been in her life to that point. Completely trusts the player and wants to make him/her as happy as she is.
# AFFECTIONATE (100 up to 399)
#     Glad that the relationship is working out and has high hopes and at this point has no doubts about whether or not it was worth it.
# HAPPY (030 up to 99)
#     Happy with how it is, could be happier but not sad at all.
# NORMAL (-29 up to 29)
#     Has mild doubts as to whether or not her sacrifices were worth it but trusts the player to treat her right. Isn't strongly happy or sad
# UPSET (-74 up to -30)
#     Feeling emotionally hurt, starting to have doubts about whether or not the player loves her and whether or not she she was right regarding what she did in the game.
# DISTRESSED (-99 up to -75)
#     Convinced the player probably doesn't love her and that she may never escape to our reality.
# BROKEN  (-100 and lower)
#     Believes that not only does the player not love her but that s/he probably hates her too because of she did and is trying to punish her. Scared of being alone in her own reality, as well as for her future.
#############

init python:
    # need to initially define this so it can be used in topic / event creation
    # NOTE: these are not updated until after aff progpoints so dont use this
    #   in aff prog points.
    mas_curr_affection = store.mas_affection.NORMAL
    mas_curr_affection_group = store.mas_affection.G_NORMAL

init -900 python in mas_affection:
    # this is very early because they are importnat constants

    # numerical constants of affection levels
    BROKEN = 1
    DISTRESSED = 2
    UPSET = 3
    NORMAL = 4
    HAPPY = 5
    AFFECTIONATE = 6
    ENAMORED = 7
    LOVE = 8

    # natural order of affection levels
    _aff_order = [
        BROKEN,
        DISTRESSED,
        UPSET,
        NORMAL,
        HAPPY,
        AFFECTIONATE,
        ENAMORED,
        LOVE
    ]

    # dict map of affection levels. This is purely for O(1) checking
    _aff_level_map = {}
    for _item in _aff_order:
        _aff_level_map[_item] = _item

    # cascade map of affection levels
    # basically, given a level, which is the next level closet to NORMAL
    _aff_cascade_map = {
        BROKEN: DISTRESSED,
        DISTRESSED: UPSET,
        UPSET: NORMAL,
        HAPPY: NORMAL,
        AFFECTIONATE: HAPPY,
        ENAMORED: AFFECTIONATE,
        LOVE: ENAMORED
    }


    # numerical constants of affection groups
    G_SAD = -1
    G_HAPPY = -2
    G_NORMAL = -3

    # natural order of affection groups
    _affg_order = [
        G_SAD,
        G_NORMAL,
        G_HAPPY
    ]

    # cascade map of affection groups
    # basically, given a group , which is the next group closet to Normal
    _affg_cascade_map = {
        G_SAD: G_NORMAL,
        G_HAPPY: G_NORMAL
    }

    # Forced expression map. This is for spaceroom dissolving
    FORCE_EXP_MAP = {
        BROKEN: "monika 6ckc_static",
        DISTRESSED: "monika 6rkc_static",
        UPSET: "monika 2esc_static",
        NORMAL: "monika 1eua_static",
        AFFECTIONATE: "monika 1eua_static",
        ENAMORED: "monika 1hua_static",
        LOVE: "monika 1hua_static",
    }

    # compare functions for affection / group
    def _compareAff(aff_1, aff_2):
        """
        See mas_compareAff for explanation
        """
        # it's pretty easy to tell if we have been given the same items
        if aff_1 == aff_2:
            return 0

        # otherwise, need to check for aff existence to get index
        if aff_1 not in _aff_order or aff_2 not in _aff_order:
            return 0

        # otherwise both proivded affections exist, lets index
        if _aff_order.index(aff_1) < _aff_order.index(aff_2):
            return -1

        return 1


    def _compareAffG(affg_1, affg_2):
        """
        See mas_compareAffG for explanation
        """
        # same stuff?
        if affg_1 == affg_2:
            return 0

        # check for aff group exist
        if affg_1 not in _affg_order or affg_2 not in _affg_order:
            return 0

        # otherwise, both groups exist, index
        if _affg_order.index(affg_1) < _affg_order.index(affg_2):
            return -1

        return 1


    def _betweenAff(aff_low, aff_check, aff_high):
        """
        checks if the given affection level is between the given low and high.
        See mas_betweenAff for explanation
        """
        aff_check = _aff_level_map.get(aff_check, None)

        # sanity checks
        if aff_check is None:
            # aff_check not a valid affection?
            return False

        # clean the affection compares
        aff_low = _aff_level_map.get(aff_low, None)
        aff_high = _aff_level_map.get(aff_high, None)

        if aff_low is None and aff_high is None:
            # if both items are None, we basically assume that both bounds
            # are set to unlimited.
            return True

        if aff_low is None:
            # dont care about the lower bound, so check if lower than
            # higher bound
            return _compareAff(aff_check, aff_high) <= 0

        if aff_high is None:
            # dont care about the upper bound, so check if higher than lower
            # bound
            return _compareAff(aff_check, aff_low) >= 0

        # otherwise, both low and high ranges are not None, so we
        # can actually check between the 2
        comp_low_high = _compareAff(aff_low, aff_high)
        if comp_low_high > 0:
            # low is actually greater than high. Therefore, the given
            # affection cannot possible be between the 2, probably.
            return False

        if comp_low_high == 0:
            # they are the same, just check for equivalence
            return _compareAff(aff_low, aff_check) == 0

        # otherwise, we legit need to check range
        return (
            _compareAff(aff_low, aff_check) <= 0
            and _compareAff(aff_check, aff_high) <= 0
        )


    def _isValidAff(aff_check):
        """
        Returns true if the given affection is a valid affection state

        NOTE: None is considered valid
        """
        if aff_check is None:
            return True

        return aff_check in _aff_level_map


    def _isValidAffRange(aff_range):
        """
        Returns True if the given aff range is a valid aff range.

        IN:
            aff_range - tuple of the following format:
                [0]: lower bound
                [1]: upper bound
            NOTE: Nones are considerd valid.
        """
        if aff_range is None:
            return True

        low, high = aff_range

        if not _isValidAff(low):
            return False

        if not _isValidAff(high):
            return False

        if low is None and high is None:
            return True

        return _compareAff(low, high) <= 0


    # thresholds values

    # Affection experience changer thresholds
    AFF_MAX_POS_TRESH = 100
    AFF_MIN_POS_TRESH = 30
    AFF_MIN_NEG_TRESH = -30
    AFF_MAX_NEG_TRESH = -75

    # Affection levels thresholds
    AFF_BROKEN_MIN = -100
    AFF_DISTRESSED_MIN = -75
    AFF_UPSET_MIN = -30
    AFF_HAPPY_MIN = 30
    AFF_AFFECTIONATE_MIN = 100
    AFF_ENAMORED_MIN = 400
    AFF_LOVE_MIN = 1000

    # Affection general mood threshold
    AFF_MOOD_HAPPY_MIN = 30
    AFF_MOOD_SAD_MIN = -30

    # lower affection cap for time
    AFF_TIME_CAP = -101


init -1 python in mas_affection:
    import os
    import datetime
    import store.mas_utils as mas_utils
    import store

    # affection log rotate
    #  we do rotations every 100 sessions
    #if store.persistent._mas_affection_log_counter is None:
    #    # start counter if None
    #    store.persistent._mas_affection_log_counter = 0

    #elif store.persistent._mas_affection_log_counter >= 500:
    #    # if 500 sessions, do a logrotate
    #    mas_utils.logrotate(
    #        os.path.normcase(renpy.config.basedir + "/log/"),
    #        "aff_log.txt"
    #    )
    #    store.persistent._mas_affection_log_counter = 0

    #else:
    #    # otherwise increase counter
    #    store.persistent._mas_affection_log_counter += 1

    # affection log setup
    log = store.mas_logging.init_log(
        "aff_log",
        formatter=store.mas_logging.logging.Formatter(
            fmt="[%(asctime)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ),
        rotations=50
    )

    # LOG messages
    # [current datetime]: monikatopic | magnitude | prev -> new
    _audit = "{0} | {1} | {2} -> {3}"

    # [current_datetime]: !FREEZE! | monikatopic | magnitude | prev -> new
    _audit_f = "{4} | {0} | {1} | {2} -> {3}"
    _freeze_text = "!FREEZE!"
    _bypass_text = "!BYPASS!"

    def audit(change, new, frozen=False, bypass=False, ldsv=None):
        """
        Audits a change in affection.

        IN:
            change - the amount we are changing by
            new - what the new affection value will be
            frozen - True means we were frozen, false measn we are not
            bypass - True means we bypassed, false means we did not
            ldsv - Set to the string to use instead of monikatopic
                NOTE: for load / save operations ONLY
        """
        if ldsv is None:
            piece_one = store.persistent.current_monikatopic
        else:
            piece_one = ldsv

        if frozen:

            # decide what piece 5 is
            if bypass:
                piece_five = _bypass_text
            else:
                piece_five = _freeze_text


            audit_text = _audit_f.format(
                piece_one,
                change,
                store._mas_getAffection(),
                new,
                piece_five
            )

        else:
            audit_text = _audit.format(
                piece_one,
                change,
                store._mas_getAffection(),
                new
            )

        log.info(audit_text)


    def raw_audit(old, new, change, tag):
        """
        Non affection-dependent auditing for general usage.

        IN:
            old - the "old" value
            new - the "new" value
            change - the chnage amount
            tag - a string to label this audit change
        """
        log.info(_audit.format(
            tag,
            change,
            old,
            new
        ))


    def txt_audit(tag, msg):
        """
        Generic auditing in the aff log

        IN:
            tag - a string to label thsi audit
            msg - message to show
        """
        log.info("{0} | {1}".format(
            tag,
            msg
        ))


    # forced expression logic function
    def _force_exp():
        """
        Determines appropriate forced expression for current affection.
        """
        curr_aff = store.mas_curr_affection

        if store.mas_isMoniNormal() and store.mas_isBelowZero():
            # special case
            return "monika 1esc_static"

        return FORCE_EXP_MAP.get(curr_aff, "monika idle")

# This needs to be defined a bit later
init 5 python in mas_affection:
    # Rand chatter settings map
    RANDCHAT_RANGE_MAP = {
        BROKEN: store.mas_randchat.RARELY,
        DISTRESSED: store.mas_randchat.OCCASIONALLY,
        UPSET: store.mas_randchat.LESS_OFTEN,
        NORMAL: store.mas_randchat.NORMAL,
        HAPPY: store.mas_randchat.NORMAL,
        AFFECTIONATE: store.mas_randchat.OFTEN,
        ENAMORED: store.mas_randchat.VERY_OFTEN,
        LOVE: store.mas_randchat.VERY_OFTEN
    }


# need these utility functiosn post event_handler
init 15 python in mas_affection:
    import store # global
    import store.evhand as evhand
    import store.mas_selspr as mas_selspr
    import store.mas_layout as mas_layout
    persistent = renpy.game.persistent
    layout = store.layout

    # programming point order:
    # 1. affection state transition code is run
    # 2. Affection state is set
    # 3. affection group transition code is run
    # 4. Affection group is set
    #
    # if affection jumps over multiple states, we run the transition code
    # in order

    # programming points
##### [AFF010] AFFECTION PROGRAMMING POINTS ###################################
    # use these to do spoecial code stuffs
    def _brokenToDis():
        """
        Runs when transitioning from broken to distressed
        """
        # change quit message
        layout.QUIT_YES = mas_layout.QUIT_YES_DIS
        layout.QUIT_NO = mas_layout.QUIT_NO_UPSET
        layout.QUIT = mas_layout.QUIT

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        # Update idle exp
        store.mas_moni_idle_disp.update()


    def _disToBroken():
        """
        Runs when transitioning from distressed to broken
        """
        # change quit message
        layout.QUIT_YES = mas_layout.QUIT_YES_BROKEN
        layout.QUIT_NO = mas_layout.QUIT_NO_BROKEN
        layout.QUIT = mas_layout.QUIT_BROKEN

        #Change randchat
        store.mas_randchat.reduceRandchatForAff(BROKEN)

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        # Update idle exp
        store.mas_moni_idle_disp.update()


    def _disToUpset():
        """
        Runs when transitioning from distressed to upset
        """
        # change quit message
        layout.QUIT_YES = mas_layout.QUIT_YES

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        # Update idle exp
        store.mas_moni_idle_disp.update()


    def _upsetToDis():
        """
        Runs when transitioning from upset to distressed
        """
        # change quit message
        layout.QUIT_YES = mas_layout.QUIT_YES_DIS
        if persistent._mas_acs_enable_promisering:
            renpy.store.monika_chr.remove_acs(renpy.store.mas_acs_promisering)
            persistent._mas_acs_enable_promisering = False

        #Change randchat
        store.mas_randchat.reduceRandchatForAff(DISTRESSED)

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        # even on special event days, if going to dis, change to def
        if store.monika_chr.clothes != store.mas_clothes_def:
            store.pushEvent("mas_change_to_def",skipeval=True)

        # Update idle exp
        store.mas_moni_idle_disp.update()


    def _upsetToNormal():
        """
        Runs when transitioning from upset to normal
        """
        # change quit message
        layout.QUIT_NO = mas_layout.QUIT_NO

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        #Check the song analysis delegate
        store.mas_songs.checkSongAnalysisDelegate()

        # Update idle exp
        store.mas_moni_idle_disp.update()


    def _normalToUpset():
        """
        Runs when transitioning from normal to upset
        """
        # change quit message
        layout.QUIT_NO = mas_layout.QUIT_NO_UPSET

        #Change randchat
        store.mas_randchat.reduceRandchatForAff(UPSET)

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        # Update idle exp
        store.mas_moni_idle_disp.update()


    def _normalToHappy():
        """
        Runs when transitioning from noraml to happy
        """
        # change quit messages
        layout.QUIT_NO = mas_layout.QUIT_NO_HAPPY

        # enable text speed
        if persistent._mas_text_speed_enabled:
            store.mas_enableTextSpeed()

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        # queue the blazerless intro event
        if not store.seen_event("mas_blazerless_intro") and not store.mas_hasSpecialOutfit():
            store.queueEvent("mas_blazerless_intro")

        # unlock blazerless for use
        store.mas_selspr.unlock_clothes(store.mas_clothes_blazerless)

        # remove change to def outfit event in case it's been pushed
        store.mas_rmallEVL("mas_change_to_def")

        #Check the song analysis delegate
        store.mas_songs.checkSongAnalysisDelegate(HAPPY)

        # Update idle exp
        store.mas_moni_idle_disp.update()


    def _happyToNormal():
        """
        Runs when transitinong from happy to normal
        """
        # change quit messages
        layout.QUIT_NO = mas_layout.QUIT_NO

        # disable text speed
        store.mas_disableTextSpeed()

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        # if not wearing def, change to def
        if store.monika_chr.clothes != store.mas_clothes_def and not store.mas_hasSpecialOutfit():
            store.pushEvent("mas_change_to_def",skipeval=True)

        #Check the song analysis delegate
        store.mas_songs.checkSongAnalysisDelegate(NORMAL)

        # Update idle exp
        store.mas_moni_idle_disp.update()


    def _happyToAff():
        """
        Runs when transitioning from happy to affectionate
        """
        # change quit messages
        layout.QUIT_YES = mas_layout.QUIT_YES_AFF
        if persistent.gender == "M" or persistent.gender == "F":
            layout.QUIT_NO = mas_layout.QUIT_NO_AFF_G
        else:
            layout.QUIT_NO = mas_layout.QUIT_NO_AFF_GL
        layout.QUIT = mas_layout.QUIT_AFF

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        #Check the song analysis delegate
        store.mas_songs.checkSongAnalysisDelegate(AFFECTIONATE)

        # Update idle exp
        store.mas_moni_idle_disp.update()

    def _affToHappy():
        """
        Runs when transitioning from affectionate to happy
        """
        # change quit messages
        layout.QUIT_YES = mas_layout.QUIT_YES
        layout.QUIT_NO = mas_layout.QUIT_NO_HAPPY
        layout.QUIT = mas_layout.QUIT

        # revert nickname
        # TODO: we should actually push an event where monika asks player not
        # to call them a certain nickname. Also this change should probaly
        # happen from normal to upset instead since thats more indicative of
        # growing animosity toward someone
        # NOTE: maybe instead of pushing an event, we could also add a pool
        # event so player can ask what happened to the nickname
        persistent._mas_monika_nickname = "Monika"
        store.m_name = persistent._mas_monika_nickname

        #Change randchat
        store.mas_randchat.reduceRandchatForAff(HAPPY)

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        #Check the song analysis delegate
        store.mas_songs.checkSongAnalysisDelegate(HAPPY)

        # Update idle exp
        store.mas_moni_idle_disp.update()

    def _affToEnamored():
        """
        Runs when transitioning from affectionate to enamored
        """
        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        #Check the song analysis delegate
        store.mas_songs.checkSongAnalysisDelegate(ENAMORED)

        # Update idle exp
        store.mas_moni_idle_disp.update()

    def _enamoredToAff():
        """
        Runs when transitioning from enamored to affectionate
        """
        #Change randchat
        store.mas_randchat.reduceRandchatForAff(AFFECTIONATE)

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        #Check the song analysis delegate
        store.mas_songs.checkSongAnalysisDelegate(AFFECTIONATE)

        # Update idle exp
        store.mas_moni_idle_disp.update()

    def _enamoredToLove():
        """
        Runs when transitioning from enamored to love
        """
        # change quit message
        layout.QUIT_NO = mas_layout.QUIT_NO_LOVE

        # unlock thanks compliement
        store.mas_unlockEventLabel("mas_compliment_thanks", eventdb=store.mas_compliments.compliment_database)

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        #Check the song analysis delegate
        store.mas_songs.checkSongAnalysisDelegate(LOVE)

        # Update idle exp
        store.mas_moni_idle_disp.update()

    def _loveToEnamored():
        """
        Runs when transitioning from love to enamored
        """
        # lock thanks compliment
        if store.seen_event("mas_compliment_thanks"):
            store.mas_lockEventLabel("mas_compliment_thanks", eventdb=store.mas_compliments.compliment_database)

        # always rebuild randos
        store.mas_idle_mailbox.send_rebuild_msg()

        #Check the song analysis delegate
        store.mas_songs.checkSongAnalysisDelegate(ENAMORED)

        # Update idle exp
        store.mas_moni_idle_disp.update()

    def _gSadToNormal():
        """
        Runs when transitioning from sad group to normal group
        """
        return


    def _gNormalToSad():
        """
        Runs when transitioning from normal group to sad group
        """
        return


    def _gNormalToHappy():
        """
        Runs when transitioning from normal group to happy group
        """
        return


    def _gHappyToNormal():
        """
        Runs when transitioning from happy group to normal group
        """
        return

###############################################################################

    # transition programing point dict
    # each item has a tuple value:
    #   [0] - going up transition pp
    #   [1] - going down transition pp
    # if a tuple value is None, it doesn't have that pp
    #
    # The key should be the affection state you are COMING FROM
    _trans_pps = {
        BROKEN: (_brokenToDis, None),
        DISTRESSED: (_disToUpset, _disToBroken),
        UPSET: (_upsetToNormal, _upsetToDis),
        NORMAL: (_normalToHappy, _normalToUpset),
        HAPPY: (_happyToAff, _happyToNormal),
        AFFECTIONATE: (_affToEnamored, _affToHappy),
        ENAMORED: (_enamoredToLove, _enamoredToAff),
        LOVE: (None, _loveToEnamored)
    }

    # same as above, except for groups
    _transg_pps = {
        G_SAD: (_gSadToNormal, None),
        G_NORMAL: (_gNormalToHappy, _gNormalToSad),
        G_HAPPY: (None, _gHappyToNormal)
    }


    def runAffPPs(start_aff, end_aff):
        """
        Runs programming points to transition from the starting affection
        to the ending affection

        IN:
            start_aff - starting affection
            end_aff - ending affection
        """
        comparison = _compareAff(start_aff, end_aff)
        if comparison == 0:
            # dont do anything if same
            return

        # otherwise, now we need to do things
        start_index = _aff_order.index(start_aff)
        end_index = _aff_order.index(end_aff)
        if comparison < 0:
            for index in range(start_index, end_index):
                to_up, to_down = _trans_pps[_aff_order[index]]
                if to_up is not None:
                    to_up()

        else:
            for index in range(start_index, end_index, -1):
                to_up, to_down = _trans_pps[_aff_order[index]]
                if to_down is not None:
                    to_down()

        # finally, rebuild the event lists
        store.mas_rebuildEventLists()


    def runAffGPPs(start_affg, end_affg):
        """
        Runs programming points to transition from the starting affection group
        to the ending affection group

        IN:
            start_affg - starting affection group
            end_affg - ending affection group
        """
        comparison = _compareAffG(start_affg, end_affg)
        if comparison == 0:
            # dont do anything if same
            return

        # otherwise, now we need to do things
        start_index = _affg_order.index(start_affg)
        end_index = _affg_order.index(end_affg)
        if comparison < 0:
            for index in range(start_index, end_index):
                to_up, to_down = _transg_pps[_affg_order[index]]
                if to_up is not None:
                    to_up()

        else:
            for index in range(start_index, end_index, -1):
                to_up, to_down = _transg_pps[_affg_order[index]]
                if to_down is not None:
                    to_down()


    def _isMoniState(aff_1, aff_2, lower=False, higher=False):
        """
        Compares the given affection values according to the affection
        state system

        By default, this will check if aff_1 == aff_2

        IN:
            aff_1 - affection to compare
            aff_2 - affection to compare
            lower - True means we want to check aff_1 <= aff_2
            higher - True means we want to check aff_1 >= aff_2

        RETURNS:
            True if the given affections pass the test we want to do.
            False otherwise
        """
        comparison = _compareAff(aff_1, aff_2)

        if comparison == 0:
            return True

        if lower:
            return comparison <= 0

        if higher:
            return comparison >= 0

        return False


    def _isMoniStateG(affg_1, affg_2, lower=False, higher=False):
        """
        Compares the given affection groups according to the affection group
        system

        By default, this will check if affg_1 == affg_2

        IN:
            affg_1 - affection group to compare
            affg_2 - affection group to compare
            lower - True means we want to check affg_1 <= affg_2
            higher - True means we want to check affg_1 >= affg_2

        RETURNS:
            true if the given affections pass the test we want to do.
            False otherwise
        """
        comparison = _compareAffG(affg_1, affg_2)

        if comparison == 0:
            return True

        if lower:
            return comparison <= 0

        if higher:
            return comparison >= 0

        return False

    ### talk and play menu stuff
    # [AFF015]
    #
    # initial contributions by:
    #   @jmwall24
    #   @multimokia

    talk_menu_quips = dict()
    play_menu_quips = dict()

    def _init_talk_quips():
        """
        Initializes the talk quiplists
        """
        global talk_menu_quips
        def save_quips(_aff, quiplist):
            mas_ql = store.MASQuipList(allow_label=False)
            for _quip in quiplist:
                mas_ql.addLineQuip(_quip)
            talk_menu_quips[_aff] = mas_ql


        ## BROKEN quips
        quips = [
            "..."
        ]
        save_quips(BROKEN, quips)

        ## DISTRESSED quips
        quips = [
            _("..."),
            _("Да?"),
            _("Ох..."),
            _("Хах..."),
            _("Я думаю, мы можем поговорить."),
            _("Ты хочешь поговорить?"),
            _("...Продолжай."),
            _("Ты уверен, что хочешь поговорить со мной?"),
            _("Ты действительно хочешь поговорить со мной?"),
            _("Хорошо...{w=0.3}если ты этого хочешь."),
            _("Это действительно то, чего ты хочешь?"),
        ]
        save_quips(DISTRESSED, quips)

        ## UPSET quips
        quips = [
            _("..."),
            _("Что?"),
            _("Хах?"),
            _("Да?"),
            _("Чего ты хочешь?"),
            _("Что теперь?"),
            _("Что же это такое?"),
            _("Продолжай."),
            _("Я надеюсь, что это важно."),
            _("Что-нибудь на уме?"),
            _("Да, [player]?"),
        ]
        save_quips(UPSET, quips)

        ## NORMAL quips
        quips = [
            _("О чём бы ты хотел поговорить?"),
            _("О чём ты думаешь?"),
            _("Есть ли что-то, о чём ты хотел бы поговорить?"),
            _("О чём ты думаешь?"),
            _("Да, [player]?"),
        ]
        save_quips(NORMAL, quips)

        ## HAPPY quips
        quips = [
            _("О чём бы ты хотел поговорить?"),
            _("О чем ты думаешь?"),
            _("Есть ли что-то, о чем ты хотел бы поговорить?"),
            _("О чём ты думаешь?"),
            _("Хочешь поболтать, [player]?"),
            _("Да, [player]?"),
            _("Что у тебя на уме, [player]?"),
            _("Как дела, [player]?"),
            _("Спрашивай, [player]."),
            _("Не стесняйся, [player]."),
        ]
        save_quips(HAPPY, quips)

        ## AFFECTIONATE quips
        quips = [
            _("О чём бы ты хотел поговорить?"),
            _("О чём бы ты хотел поговорить, [mas_get_player_nickname()]?"),
            _("О чём ты думаешь?"),
            _("Есть ли что-то, о чем ты хотел бы поговорить, [mas_get_player_nickname()]?"),
            _("Что-то на уме?"),
            _("Что-то на уме, [mas_get_player_nickname()]?"),
            _("Не против поболтать, [mas_get_player_nickname()]?"),
            _("Да, [mas_get_player_nickname()]?"),
            _("Что у тебя на уме, [mas_get_player_nickname()]?"),
            _("Как дела, [mas_get_player_nickname()]?"),
            _("Спрашивай, [mas_get_player_nickname()]."),
            _("Не стесняйся, [mas_get_player_nickname()]~"),
            _("Я вся во внимание, [mas_get_player_nickname()]~"),
            _("Конечно, мы можем поговорить, [mas_get_player_nickname()]."),
        ]
        save_quips(AFFECTIONATE, quips)

        ## ENAMORED quips
        quips = [
            _("О чем бы ты хотел поговорить? <3"),
            _("О чем бы ты хотел поговорить, [mas_get_player_nickname()]? <3"),
            _("О чём ты думаешь?"),
            _("Есть ли что-то, о чем ты хотел бы поговорить, [mas_get_player_nickname()]?"),
            _("Что-то на уме?"),
            _("Что-то на уме, [mas_get_player_nickname()]?"),
            _("Как я вижу, ты хочешь поболтать~"),
            _("Да, [mas_get_player_nickname()]?"),
            _("Что у тебя на уме, [mas_get_player_nickname()]?"),
            _("Как дела, [player]?"),
            _("Спрашивай, [mas_get_player_nickname()]~"),
            _("Я вся во внимание, [mas_get_player_nickname()]~"),
            _("Конечно, мы можем поговорить, [mas_get_player_nickname()]~"),
            _("Уделяй себе столько времени, сколько тебе нужно, [player]."),
            _("Мы можем поговорить обо всем, о чем ты захочешь, [mas_get_player_nickname()]."),
        ]
        save_quips(ENAMORED, quips)

        ## LOVE quips
        quips = [
            _("О чем бы ты хотел поговорить? <3"),
            _("О чем бы ты хотел поговорить, [mas_get_player_nickname()]? <3"),
            _("О чём ты думаешь?"),
            _("Что-то на уме?"),
            _("Что-то на уме, [mas_get_player_nickname()]?"),
            _("Как я вижу, ты хочешь поболтать~"),
            _("Да, [mas_get_player_nickname()]?"),
            _("Что у тебя на уме, [mas_get_player_nickname()]?"),
            _("<3"),
            _("Как дела, [mas_get_player_nickname()]?"),
            _("Спрашивай, [mas_get_player_nickname()]~"),
            _("Я вся во внимание, [mas_get_player_nickname()]~"),
            _("Мы можем поговорить обо всем, о чем ты захочешь, [mas_get_player_nickname()]."),
            _("Конечно, мы можем поговорить, [mas_get_player_nickname()]~"),
            _("Уделяй себе столько времени, сколько тебе нужно, [mas_get_player_nickname()]~"),
            _("Я вся твоя, [mas_get_player_nickname()]~"),
            _("О? Что-то...{w=0.3}{i}важное{/i} у тебя на уме, [mas_get_player_nickname()]?~"),
        ]
        save_quips(LOVE, quips)


    def _init_play_quips():
        """
        Initializes the play quipliust
        """
        global play_menu_quips
        def save_quips(_aff, quiplist):
            mas_ql = store.MASQuipList(allow_label=False)
            for _quip in quiplist:
                mas_ql.addLineQuip(_quip)
            play_menu_quips[_aff] = mas_ql


        ## BROKEN quips
        quips = [
            _("...")
        ]
        save_quips(BROKEN, quips)

        ## DISTRESSED quips
        quips = [
            _("..."),
            _("Если это то, чего ты хочешь..."),
            _("Думаю, не помешает попробовать..."),
            _("...Правда?"),
        ]
        save_quips(DISTRESSED, quips)

        ## UPSET quips
        quips = [
            _("..."),
            _("Если это то, чего ты хочешь..."),
            _("...Правда?"),
            _("О, хорошо..."),
        ]
        save_quips(UPSET, quips)

        ## NORMAL quips
        quips = [
            _("Что бы ты хотел сыграть?"),
            _("Есть ли у тебя что-то на примете?"),
            _("Есть что-то конкретное, что ты хотел бы сыграть?"),
            _("Во что бы нам сегодня поиграть, [player]?"),
            _("Конечно, я готова поиграть."),
        ]
        save_quips(NORMAL, quips)

        ## HAPPY quips
        quips = [
            _("Что бы ты хотел сыграть?"),
            _("Есть ли у тебя что-то на примете?"),
            _("AЕсть что-то конкретное, что ты хотел бы сыграть?"),
            _("Во что бы нам сегодня поиграть, [player]?"),
            _("Конечно, я готова поиграть!"),
        ]
        save_quips(HAPPY, quips)

        ## AFFECTIONATE quips
        quips = [
            _("Что бы ты хотел сыграть?"),
            _("Выбирай всё, что тебе нравится, [mas_get_player_nickname()]."),
            _("Во что бы нам сегодня поиграть, [mas_get_player_nickname()]?"),
            _("Конечно, я готова поиграть!"),
            _("Выбирай любую игру, которая тебе нравится."),
        ]
        save_quips(AFFECTIONATE, quips)

        ## ENAMORED quips
        quips = [
            _("Во что бы ты хотел поиграть? <3"),
            _("Выбери игру, любую игру~"),
            _("Выбирай любую игру, которая тебе нравится, [mas_get_player_nickname()]."),
            _("Выбери всё, что тебе нравится, [mas_get_player_nickname()]."),
        ]
        save_quips(ENAMORED, quips)

        ## LOVE quips
        quips = [
            _("Что бы ты хотел сыграть? <3"),
            _("Выбирай любую игру, которая тебе нравится, [mas_get_player_nickname()]."),
            _("Выбери всё, что тебе нравится, [mas_get_player_nickname()]."),
            _("Выбери игру, любую игр~"),
            _("Я бы с удовольствием сыграла с тобой во что-нибудь, [mas_get_player_nickname()]~"),
            _("Конечно, я с удовольствием поиграю с тобой!"),
            _("Я всегда буду рада поиграть с тобой, [mas_get_player_nickname()]~"),
        ]
        save_quips(LOVE, quips)

    _init_talk_quips()
    _init_play_quips()


    def _dict_quip(_quips):
        """
        Returns a quip based on the current affection using the given quip
        dict

        IN:
            _quips - quip dict to pull from

        RETURNS:
            quip or empty string if failure
        """
        quipper = _quips.get(store.mas_curr_affection, None)
        if quipper is not None:
            return quipper.quip()

        return ""


    def talk_quip():
        """
        Returns a talk quip based on the current affection
        """
        quip = _dict_quip(talk_menu_quips)
        if len(quip) > 0:
            return quip
        return _("О чем бы ты хотел поговорить?")


    def play_quip():
        """
        Returns a play quip based on the current affection
        """
        quip = _dict_quip(play_menu_quips)
        if len(quip) > 0:
            return quip
        return _("Во что бы ты хотел поиграть?")



default persistent._mas_long_absence = False
default persistent._mas_pctaieibe = None
default persistent._mas_pctaneibe = None
default persistent._mas_pctadeibe = None
default persistent._mas_aff_backup = None

init -10 python:
    if persistent._mas_aff_mismatches is None:
        persistent._mas_aff_mismatches = 0

    def _mas_AffSave():
        aff_value = _mas_getAffection()
        #inum, nnum, dnum = mas_utils._splitfloat(aff_value)
        #persistent._mas_pctaieibe = bytearray(mas_utils._itoIS(inum))
        #persistent._mas_pctaneibe = bytearray(mas_utils._itoIS(nnum))
        #persistent._mas_pctadeibe = bytearray(mas_utils._itoIS(dnum))

        # reset
        persistent._mas_pctaieibe = None
        persistent._mas_pctaneibe = None
        persistent._mas_pctadeibe = None

        # audit this change
        store.mas_affection.audit(aff_value, aff_value, ldsv="SAVE")

        # backup this value
        if persistent._mas_aff_backup != aff_value:
            store.mas_affection.raw_audit(
                persistent._mas_aff_backup,
                aff_value,
                aff_value,
                "SET BACKUP"
            )
            persistent._mas_aff_backup = aff_value


    def _mas_AffLoad():
        #new_value = 0
        #if (
        #        persistent._mas_pctaieibe is not None
        #        and persistent._mas_pctaneibe is not None
        #        and persistent._mas_pctadeibe is not None
        #    ):
        #    try:
        #        inum = mas_utils._IStoi(
        #            mas_utils.ISCRAM.from_buffer(persistent._mas_pctaieibe)
        #        )
        #        nnum = mas_utils._IStoi(
        #            mas_utils.ISCRAM.from_buffer(persistent._mas_pctaneibe)
        #        )
        #        dnum = float(mas_utils._IStoi(
        #            mas_utils.ISCRAM.from_buffer(persistent._mas_pctadeibe)
        #        ))
        #        if inum < 0:
        #            new_value = inum - (nnum / dnum)
        #        else:
        #            new_value = inum + (nnum / dnum)
#
#            except:
#                # dont break me yo
#                new_value = 0
#
        # reset
        persistent._mas_pctaieibe = None
        persistent._mas_pctaneibe = None
        persistent._mas_pctadeibe = None

        # pull numerical afffection for audting
        if (
                persistent._mas_affection is None
                or "affection" not in persistent._mas_affection
            ):
            if persistent._mas_aff_backup is None:
                new_value = 0
                store.mas_affection.txt_audit("LOAD", "No backup found")

            else:
                new_value = persistent._mas_aff_backup
                store.mas_affection.txt_audit("LOAD", "Loading from backup")

        else:
            new_value = persistent._mas_affection["affection"]
            store.mas_affection.txt_audit("LOAD", "Loading from system")

        # audit the amount loaded
        store.mas_affection.raw_audit(0, new_value, new_value, "LOAD?")

        # if the back is None, set the backup
        if persistent._mas_aff_backup is None:
            persistent._mas_aff_backup = new_value

            # audit
            store.mas_affection.raw_audit(
                "None",
                new_value,
                new_value,
                "NEW BACKUP"
            )


        else:
            # restore from backup if we have a mismatch
            if new_value != persistent._mas_aff_backup:
                persistent._mas_aff_mismatches += 1
                store.mas_affection.txt_audit(
                    "MISMATCHES",
                    persistent._mas_aff_mismatches
                )
                store.mas_affection.raw_audit(
                    new_value,
                    persistent._mas_aff_backup,
                    persistent._mas_aff_backup,
                    "RESTORE"
                )
                new_value = persistent._mas_aff_backup

        # audit this change
        store.mas_affection.audit(new_value, new_value, ldsv="LOAD COMPLETE")

        # and set what we got
        persistent._mas_affection["affection"] = new_value


# need to have affection initlaized post event_handler
init 20 python:

    import datetime
    import store.mas_affection as affection
    import store.mas_utils as mas_utils

    # Functions to freeze exp progression for story events, use wisely.
    def mas_FreezeGoodAffExp():
        persistent._mas_affection_goodexp_freeze = True

    def mas_FreezeBadAffExp():
        persistent._mas_affection_badexp_freeze = True

    def mas_FreezeBothAffExp():
        mas_FreezeGoodAffExp()
        mas_FreezeBadAffExp()

    def mas_UnfreezeBadAffExp():
        persistent._mas_affection_badexp_freeze = False

    def mas_UnfreezeGoodAffExp():
        persistent._mas_affection_goodexp_freeze = False

    def mas_UnfreezeBothExp():
        mas_UnfreezeBadAffExp()
        mas_UnfreezeGoodAffExp()


    # getter
    def _mas_getAffection():
        if persistent._mas_affection is not None:
            return persistent._mas_affection.get(
                "affection",
                persistent._mas_aff_backup
            )

        return persistent._mas_aff_backup


    def _mas_getBadExp():
        if persistent._mas_affection is not None:
            return persistent._mas_affection.get(
                "badexp",
                1
            )
        return 1


    def _mas_getGoodExp():
        if persistent._mas_affection is not None:
            return persistent._mas_affection.get(
                "goodexp",
                1
            )
        return 1


    def _mas_getTodayExp():
        if persistent._mas_affection is not None:
            return persistent._mas_affection.get("today_exp", 0)

        return 0


    # numerical affection check
    def mas_isBelowZero():
        return _mas_getAffection() < 0


    ## affection comparison
    # [AFF020] Affection comparTos
    def mas_betweenAff(aff_low, aff_check, aff_high):
        """
        Checks if the given affection is between the given affection levels.

        If low is actually greater than high, then False is always returned

        IN:
            aff_low - the lower bound of affecton to check with (inclusive)
                if None, then we assume no lower bound
            aff_check - the affection to check
            aff_high - the upper bound of affection to check with (inclusive)
                If None, then we assume no upper bound

        RETURNS:
            True if the given aff check is within the bounds of the given
            lower and upper affection limits, False otherwise.
            If low is greater than high, False is returned.
        """
        return affection._betweenAff(aff_low, aff_check, aff_high)


    def mas_compareAff(aff_1, aff_2):
        """
        Runs compareTo logic on the given affection states

        IN:
            aff_1 - an affection state to compare
            aff_2 - an affection state to compare

        RETURNS:
            negative number if aff_1 < aff_2
            0 if aff_1 == aff_2
            postitive number if aff_1 > aff_2
            Returns 0 if a non affection state was provided
        """
        return affection._compareAff(aff_1, aff_2)


    def mas_compareAffG(affg_1, affg_2):
        """
        Runs compareTo logic on the given affection groups

        IN:
            affg_1 - an affection group to compare
            affg_2 - an affection group to compare

        RETURNS:
            negative number if affg_1 < affg_2
            0 if affg_1 == affg_2
            positive numbre if affg_1 > affg_2
            Returns 0 if a non affection group was provided
        """
        return affection._compareAffG(affg_1, affg_2)


    ## afffection state functions
    # [AFF021] Affection state comparisons
    def mas_isMoniBroken(lower=False, higher=False):
        """
        Checks if monika is broken

        IN:
            lower - True means we include everything below this affection state
                as broken as well
                (Default: False)
            higher - True means we include everything above this affection
                state as broken as well
                (Default: False)

        RETURNS:
            True if monika is broke, False otherwise
        """
        return affection._isMoniState(
            mas_curr_affection,
            store.mas_affection.BROKEN,
            higher=higher
        )


    def mas_isMoniDis(lower=False, higher=False):
        """
        Checks if monika is distressed

        IN:
            lower - True means we cinlude everything below this affection state
                as distressed as well
                NOTE: takes precedence over higher
                (Default: False)
            higher - True means we include everything above this affection
                state as distressed as well
                (Default: FAlse)

        RETURNS:
            True if monika is distressed, false otherwise
        """
        return affection._isMoniState(
            mas_curr_affection,
            store.mas_affection.DISTRESSED,
            lower=lower,
            higher=higher
        )


    def mas_isMoniUpset(lower=False, higher=False):
        """
        Checks if monika is upset

        IN:
            lower - True means we include everything below this affection
                state as upset as well
                (Default: False)
            higher - True means we include everything above this affection
                state as upset as well
                (Default: False)

        RETURNS:
            True if monika is upset, false otherwise
        """
        return affection._isMoniState(
            mas_curr_affection,
            store.mas_affection.UPSET,
            lower=lower,
            higher=higher
        )


    def mas_isMoniNormal(lower=False, higher=False):
        """
        Checks if monika is normal

        IN:
            lower - True means we include everything below this affection state
                as normal as well
                (Default: False)
            higher - True means we include evreything above this affection
                state as normal as well
                (Default: False)

        RETURNS:
            True if monika is normal, false otherwise
        """
        return affection._isMoniState(
            mas_curr_affection,
            store.mas_affection.NORMAL,
            lower=lower,
            higher=higher
        )


    def mas_isMoniHappy(lower=False, higher=False):
        """
        Checks if monika is happy

        IN:
            lower - True means we include everything below this affection
                state as happy as well
                (Default: False)
            higher - True means we include everything above this affection
                state as happy as well
                (Default: False)

        RETURNS:
            True if monika is happy, false otherwise
        """
        return affection._isMoniState(
            mas_curr_affection,
            store.mas_affection.HAPPY,
            lower=lower,
            higher=higher
        )


    def mas_isMoniAff(lower=False, higher=False):
        """
        Checks if monika is affectionate

        IN:
            lower - True means we include everything below this affection
                state as affectionate as well
                (Default: FAlse)
            higher - True means we include everything above this affection
                state as affectionate as well
                (Default: False)

        RETURNS:
            True if monika is affectionate, false otherwise
        """
        return affection._isMoniState(
            mas_curr_affection,
            store.mas_affection.AFFECTIONATE,
            lower=lower,
            higher=higher
        )


    def mas_isMoniEnamored(lower=False, higher=False):
        """
        Checks if monika is enamored

        IN:
            lower - True means we include everything below this affection
                state as enamored as well
                (Default: False)
            higher - True means we include everything above this affection
                state as enamored as well
                (Default: False)

        RETURNS:
            True if monika is enamored, false otherwise
        """
        return affection._isMoniState(
            mas_curr_affection,
            store.mas_affection.ENAMORED,
            lower=lower,
            higher=higher
        )


    def mas_isMoniLove(lower=False, higher=False):
        """
        Checks if monika is in love

        IN:
            lower - True means we include everything below this affectionate
                state as love as well
                (Default: False)
            higher - True means we include everything above this affection
                state as love as well
                (Default: False)

        RETURNS:
            True if monika in love, false otherwise
        """
        return affection._isMoniState(
            mas_curr_affection,
            store.mas_affection.LOVE,
            lower=lower
        )


    # [AFF023] Group state checkers
    def mas_isMoniGSad(lower=False, higher=False):
        """
        Checks if monika is in sad affection group

        IN:
            lower - True means we include everything below this affection
                group as sad as well
                (Default: False)
            higher - True means we include everything above this affection
                group as sad as well
                (Default: False)

        RETURNS:
            True if monika in sad group, false otherwise
        """
        return affection._isMoniStateG(
            mas_curr_affection_group,
            store.mas_affection.G_SAD,
            higher=higher
        )


    def mas_isMoniGNormal(lower=False, higher=False):
        """
        Checks if monika is in normal affection group

        IN:
            lower - True means we include everything below this affection
                group as normal as well
                (Default: False)
            higher - True means we include everything above this affection
                group as normal as well
                (Default: False)

        RETURNS:
            True if monika is in normal group, false otherwise
        """
        return affection._isMoniStateG(
            mas_curr_affection_group,
            store.mas_affection.G_NORMAL,
            lower=lower,
            higher=higher
        )


    def mas_isMoniGHappy(lower=False, higher=False):
        """
        Checks if monika is in happy affection group

        IN:
            lower - True means we include everything below this affection
                group as happy as well
                (Default: False)
            higher - True means we include everything above this affection
                group as happy as well
                (Default: FAlse)

        RETURNS:
            True if monika is in happy group, false otherwise
        """
        return affection._isMoniStateG(
            mas_curr_affection_group,
            store.mas_affection.G_HAPPY,
            lower=lower
        )


   # Used to adjust the good and bad experience factors that are used to adjust affection levels.
    def mas_updateAffectionExp(skipPP=False):
        global mas_curr_affection
        global mas_curr_affection_group

        # store the value for easiercomparisons
        curr_affection = _mas_getAffection()

        # If affection is greater then AFF_MIN_POS_TRESH, update good exp. Simulates growing affection.
        if  affection.AFF_MIN_POS_TRESH <= curr_affection:
            persistent._mas_affection["goodexp"] = 3
            persistent._mas_affection["badexp"] = 1

        # If affection is between AFF_MAX_NEG_TRESH and AFF_MIN_NEG_TRESH, update both exps. Simulates erosion of affection.
        elif affection.AFF_MAX_NEG_TRESH < curr_affection <= affection.AFF_MIN_NEG_TRESH:
            persistent._mas_affection["goodexp"] = 0.5
            persistent._mas_affection["badexp"] = 3

        # If affection is less than AFF_MIN_NEG_TRESH, update bad exp. Simulates increasing loss of affection.
        elif curr_affection <= affection.AFF_MAX_NEG_TRESH:
            persistent._mas_affection["badexp"] = 5

        # Defines an easy current affection statement to refer to so points aren't relied upon.
        new_aff = mas_curr_affection
        if curr_affection <= affection.AFF_BROKEN_MIN:
            new_aff = affection.BROKEN

        elif affection.AFF_BROKEN_MIN < curr_affection <= affection.AFF_DISTRESSED_MIN:
            new_aff = affection.DISTRESSED

        elif affection.AFF_DISTRESSED_MIN < curr_affection <= affection.AFF_UPSET_MIN:
            new_aff = affection.UPSET

        elif affection.AFF_UPSET_MIN < curr_affection < affection.AFF_HAPPY_MIN:
            new_aff = affection.NORMAL

        elif affection.AFF_HAPPY_MIN <= curr_affection < affection.AFF_AFFECTIONATE_MIN:
            new_aff = store.mas_affection.HAPPY

        elif affection.AFF_AFFECTIONATE_MIN <= curr_affection < affection.AFF_ENAMORED_MIN:
            new_aff = affection.AFFECTIONATE

        elif affection.AFF_ENAMORED_MIN <= curr_affection < affection.AFF_LOVE_MIN:
            new_aff = affection.ENAMORED

        elif curr_affection >= affection.AFF_LOVE_MIN:
            new_aff = affection.LOVE

        # run affection programming points
        if new_aff != mas_curr_affection:
            if not skipPP:
                affection.runAffPPs(mas_curr_affection, new_aff)
            mas_curr_affection = new_aff

        # A group version for general sadness or happiness
        new_affg = mas_curr_affection_group
        if curr_affection <= affection.AFF_MOOD_SAD_MIN:
            new_affg = affection.G_SAD

        elif curr_affection >= affection.AFF_MOOD_HAPPY_MIN:
            new_affg = affection.G_HAPPY

        else:
            new_affg = affection.G_NORMAL

        if new_affg != mas_curr_affection_group:
            if not skipPP:
                affection.runAffGPPs(mas_curr_affection_group, new_affg)
            mas_curr_affection_group = new_affg


    # Used to increment affection whenever something positive happens.
    def mas_gainAffection(
            amount=None,
            modifier=1,
            bypass=False
        ):

        if amount is None:
            amount = _mas_getGoodExp()

        # is it a new day?
        if mas_pastOneDay(persistent._mas_affection.get("freeze_date")):
            persistent._mas_affection["freeze_date"] = datetime.date.today()
            persistent._mas_affection["today_exp"] = 0
            mas_UnfreezeGoodAffExp()

        # calculate new value
        frozen = persistent._mas_affection_goodexp_freeze
        change = (amount * modifier)
        new_value = _mas_getAffection() + change
        if new_value > 1000000:
            new_value = 1000000

        # audit the attempted change
        affection.audit(change, new_value, frozen, bypass)

        # if we're not freezed or if the bypass flag is True
        if not frozen or bypass:
            # Otherwise, use the value passed in the argument.
            persistent._mas_affection["affection"] = new_value

            if not bypass:
                persistent._mas_affection["today_exp"] = (
                    _mas_getTodayExp() + change
                )
                if persistent._mas_affection["today_exp"] >= 7:
                    mas_FreezeGoodAffExp()

            # Updates the experience levels if necessary.
            mas_updateAffectionExp()


    # Used to subtract affection whenever something negative happens.
    # A reason can be specified and used for the apology dialogue
    # if the default value is used Monika won't comment on the reason,
    # and slightly will recover affection
    # if None is passed she won't acknowledge that there was need for an apology.
    # DEFAULTS reason to an Empty String mostly because when this one is called
    # is intended to be used for something the player can apologize for, but it's
    # not totally necessary.
    #NEW BITS:
    #prompt: the prompt shown in the menu for apologizing
    #expirydatetime:
    #generic: do we want this to be persistent? or not
    def mas_loseAffection(
            amount=None,
            modifier=1,
            reason=None,
            ev_label=None,
            apology_active_expiry=datetime.timedelta(hours=3),
            apology_overall_expiry=datetime.timedelta(weeks=1),
        ):

        if amount is None:
            amount = _mas_getBadExp()

        #set apology flag
        mas_setApologyReason(reason=reason,ev_label=ev_label,apology_active_expiry=apology_active_expiry,apology_overall_expiry=apology_overall_expiry)

        # calculate new vlaue
        frozen = persistent._mas_affection_badexp_freeze
        change = (amount * modifier)
        new_value = _mas_getAffection() - change
        if new_value < -1000000:
            new_value = -1000000

        # audit this attempted change
        affection.audit(change, new_value, frozen)

        if not frozen:
            # Otherwise, use the value passed in the argument.
            persistent._mas_affection["affection"] = new_value

            # Updates the experience levels if necessary.
            mas_updateAffectionExp()


    def mas_setAffection(amount=None, logmsg="SET"):
        """
        Sets affection to a value

        NOTE: never use this to add / lower affection unless its to
          strictly set affection to a level for some reason.

        IN:
            amount - amount to set affection to
            logmsg - msg to show in the log
                (Default: SET)
        """

#        frozen = (
#            persistent._mas_affection_badexp_freeze
#            or persistent._mas_affection_goodexp_freeze
#        )
        if amount is None:
            amount = _mas_getAffection()

        # audit the change (or attempt)
        affection.audit(amount, amount, False, ldsv=logmsg)

        # NOTE: we should NEVER freeze set affection.
        # Otherwise, use the value passed in the argument.
        persistent._mas_affection["affection"] = amount
        # Updates the experience levels if necessary.
        mas_updateAffectionExp()

    def mas_setApologyReason(
        reason=None,
        ev_label=None,
        apology_active_expiry=datetime.timedelta(hours=3),
        apology_overall_expiry=datetime.timedelta(weeks=1)
        ):
        """
        Sets a reason for apologizing

        IN:
            reason - The reason for the apology (integer value corresponding to item in the apology_reason_db)
                (if left None, and an ev_label is present, we assume a non-generic apology)
            ev_label - The apology event we want to unlock
                (required)
            apology_active_expiry - The amount of session time after which, the apology that was added expires
                defaults to 3 hours active time
            apology_overall_expiry - The amount of overall time after which, the apology that was added expires
                defaults to 7 days
        """

        global mas_apology_reason

        if ev_label is None:
            if reason is None:
                mas_apology_reason = 0
            else:
                mas_apology_reason = reason
            return
        elif mas_getEV(ev_label) is None:
            store.mas_utils.mas_log.error(
                "ev_label does not exist: {0}".format(repr(ev_label))
            )
            return

        if ev_label not in persistent._mas_apology_time_db:
            #Unlock the apology ev label
            store.mas_unlockEVL(ev_label, 'APL')

            #Calculate the current total playtime
            current_total_playtime = persistent.sessions['total_playtime'] + mas_getSessionLength()

            #Now we set up our apology dict to keep track of this so we can relock it if you didn't apologize in time
            persistent._mas_apology_time_db[ev_label] = (current_total_playtime + apology_active_expiry,datetime.date.today() + apology_overall_expiry)
            return

    # Used to check to see if affection level has reached the point where it should trigger an event while playing the game.
    def mas_checkAffection():

        curr_affection = _mas_getAffection()
        # If affection level between -15 and -20 and you haven't seen the label before, push this event where Monika mentions she's a little upset with the player.
        # This is an indicator you are heading in a negative direction.
        if curr_affection <= -15 and not seen_event("mas_affection_upsetwarn"):
            queueEvent("mas_affection_upsetwarn", notify=True)

        # If affection level between 15 and 20 and you haven't seen the label before, push this event where Monika mentions she's really enjoying spending time with you.
        # This is an indicator you are heading in a positive direction.
        elif 15 <= curr_affection and not seen_event("mas_affection_happynotif"):
            queueEvent("mas_affection_happynotif", notify=True)

        # If affection level is greater than 100 and you haven't seen the label yet, push this event where Monika will allow you to give her a nick name.
        elif curr_affection >= 100 and not seen_event("monika_affection_nickname"):
            queueEvent("monika_affection_nickname", notify=True)

        # If affection level is less than -50 and the label hasn't been seen yet, push this event where Monika says she's upset with you and wants you to apologize.
        elif curr_affection <= -50 and not seen_event("mas_affection_apology"):
            if not persistent._mas_disable_sorry:
                queueEvent("mas_affection_apology", notify=True)

    # Easy functions to add and subtract points, designed to make it easier to sadden her so player has to work harder to keep her happy.
    # Check function is added to make sure mas_curr_affection is always appropriate to the points counter.
    # Internal cooldown to avoid topic spam and Monika affection swings, the amount of time to wait before a function is effective
    # is equal to the amount of points it's added or removed in minutes.

    # Nothing to apologize for now
    mas_apology_reason = None

    def _mas_AffStartup():
        # need to load affection values from beyond the grave
        # failure to load means we reset to 0. No excuses
        _mas_AffLoad()

        # Makes the game update affection on start-up so the global variables
        # are defined at all times.
        mas_updateAffectionExp()

        if persistent.sessions["last_session_end"] is not None:
            persistent._mas_absence_time = (
                datetime.datetime.now() -
                persistent.sessions["last_session_end"]
            )
        else:
            persistent._mas_absence_time = datetime.timedelta(days=0)

        # Monika's initial affection based on start-up.
        if not persistent._mas_long_absence:
            time_difference = persistent._mas_absence_time
            # we skip this for devs since we sometimes use older
            # persistents and only apply after 1 week
            if (
                    not config.developer
                    and time_difference >= datetime.timedelta(weeks = 1)
                ):
                new_aff = _mas_getAffection() - (
                    0.5 * time_difference.days
                )
                if new_aff < affection.AFF_TIME_CAP:
                    #We can only lose so much here
                    store.mas_affection.txt_audit("ABS", "capped loss")
                    mas_setAffection(affection.AFF_TIME_CAP)

                    #If over 10 years, then we need to FF
                    if time_difference >= datetime.timedelta(days=(365 * 10)):
                        store.mas_affection.txt_audit("ABS", "10 year diff")
                        mas_loseAffection(200)

                else:
                    store.mas_affection.txt_audit("ABS", "she missed you")
                    mas_setAffection(new_aff)


# Unlocked when affection level reaches 50.
# This allows the player to choose a nick name for Monika that will be displayed on the label where Monika's name usually is.
# There is a character limit of 10 characters.
init 5 python:
    addEvent(
        Event(persistent.event_database,
            eventlabel='monika_affection_nickname',
            prompt="Бесконечные моники",
            category=['моника'],
            random=False,
            pool=True,
            unlocked=True,
            rules={"no_unlock": None},
            aff_range=(mas_aff.AFFECTIONATE, None)
        ),
        restartBlacklist=True
    )

#Whether or not the player has called Monika a bad name
default persistent._mas_pm_called_moni_a_bad_name = False

#Whether or not Monika has offered the player a nickname
default persistent._mas_offered_nickname = False

#The grandfathered nickname we'll use if the player's name is considered awkward
default persistent._mas_grandfathered_nickname = None

label monika_affection_nickname:
    python:
        #NOTE: Moni nicknames use a slightly altered list to exclude male exclusive titles/nicknames
        good_monika_nickname_comp = re.compile('|'.join(mas_good_monika_nickname_list), re.IGNORECASE)

        # for later code
        aff_nickname_ev = mas_getEV("monika_affection_nickname")

    if not persistent._mas_offered_nickname:
        m 1euc "Я тут подумала, [player]..."
        m 3eud "Ты ведь знаешь, что существует потенциально бесконечное количество Моник?"

        if renpy.seen_label('monika_clones'):
            m 3eua "В конце концов, мы уже обсуждали это раньше."

        m 3hua "Ну, я придумала решение!"
        m 3eua "Почему бы тебе не дать мне прозвище? Это сделает меня единственной Моникой во вселенной с таким именем."
        m 3eka "И это будет много значить, если ты выберешь его для меня~"
        m 3hua "Но последнее слово всё равно будет за мной!"
        m "Что скажешь?{nw}"
        python:
            if aff_nickname_ev:
                # change the prompt for this event
                aff_nickname_ev.prompt = _("Могу я называть тебя другим прозвищем?")
                Event.lockInit("prompt", ev=aff_nickname_ev)
                persistent._mas_offered_nickname = True

            #Also give the player nickname event a start_date so it doesn't queue instantly
            pnick_ev = mas_getEV("mas_affection_playernickname")
            if pnick_ev:
                pnick_ev.start_date = datetime.datetime.now() + datetime.timedelta(hours=2)

    else:
        jump monika_affection_nickname_yes

    $ _history_list.pop()
    menu:
        m "Что скажешь?{fast}"
        "Да.":
            label monika_affection_nickname_yes:
                pass

            show monika 1eua at t11 zorder MAS_MONIKA_Z

            $ done = False
            while not done:
                python:
                    inputname = mas_input(
                        _("Так как ты хочешь называть меня?"),
                        allow=name_characters_only,
                        length=10,
                        screen_kwargs={"use_return_button": True, "return_button_value": "nevermind"}
                    ).strip(' \t\n\r')

                    lowername = inputname.lower()

                # lowername isn't detecting player or m_name?
                if lowername == "Неважно":
                    m 1euc "О, понятно."
                    m 1tkc "Что ж... очень жаль."
                    m 3eka "Но ничего страшного. Мне все равно нравится '[m_name]'."
                    $ done = True

                elif not lowername:
                    m 1lksdla "..."
                    m 1hksdrb "Ты должен дать мне прозвище, [player]!"
                    m "Клянусь, иногда ты такой глупый."
                    m 1eka "Попробуй ещё раз!"

                elif lowername != "monika" and lowername == player.lower():
                    m 1euc "..."
                    m 1lksdlb "Это твоё имя, [player]! Дай мне моё собственное!"
                    m 1eka "Попробуй ещё раз~"

                elif lowername == m_name.lower():
                    m 1euc "..."
                    m 1hksdlb "Я думала, мы выбираем новое прозвище, глупышка."
                    m 1eka "Попробуй ещё раз~"


                #TODO: FIX THIS elif re.findall(r"mon[-_'\s]+ika|[^-_'\s]+monica", lowername):\
                elif re.findall(r"mon[-_'\s]+ika|monica", lowername):
                    m 2ttc "..."
                    m 2tsd "Попробуй ещё раз."
                    show monika 1esc

                elif persistent._mas_grandfathered_nickname and lowername == persistent._mas_grandfathered_nickname.lower():
                    jump .neutral_accept

                elif mas_awk_name_comp.search(inputname):
                    m 1rkc "..."
                    m 1rksdld "Хотя я не ненавижу это, я не думаю, что мне будет удобно, если ты будешь называть меня так."
                    m 1eka "Можешь выбрать что-нибудь более подходящее, [player]?"

                else:
                    if not mas_bad_name_comp.search(inputname) and lowername not in ["yuri", "sayori", "natsuki"]:
                        if lowername == "monika":
                            $ inputname = inputname.capitalize()
                            m 3hua "Эхехе, снова к классике, я вижу~"

                        elif good_monika_nickname_comp.search(inputname):
                            m 1wuo "О! Это замечательное прозвище!"
                            m 3ekbsa "Спасибо, [player]. Ты такой милый!~"

                        else:
                            label .neutral_accept:
                                pass

                            m 1duu "[inputname]... Это довольно милое прозвище."
                            m 3ekbsa "Спасибо [player], ты такой милый~"

                        $ persistent._mas_monika_nickname = inputname
                        $ m_name = inputname

                        m 1eua "Хорошо!"
                        if m_name == "Monika":
                            m 1hua "Тогда я вернусь к своему имени."

                        else:
                            m 3hua "С этого момента ты можешь называть меня '[m_name].'"
                            m 1hua "Эхехе~"
                        $ done = True

                    else:
                        #Remove the apology reason from this as we're handling the apology differently now.
                        $ mas_loseAffection(ev_label="mas_apology_bad_nickname")
                        if lowername in ["yuri", "sayori", "natsuki"]:
                            m 1wud "...!"
                            m 2wfw "Я..."
                            m "Я... не могу поверить, что ты только что сделал это, [player]."
                            m 2wfx "Ты действительно пытаешься дать мне её имя?"
                            m 2dfd ".{w=0.5}.{w=0.5}.{nw}"
                            m 2dfc ".{w=0.5}.{w=0.5}.{nw}"
                            m 2rkc "Я думала, что ты..."
                            m 2dfc "..."
                            m 2lfc "Я не могу в это поверить, [player]."
                            m 2dfc "..."
                            m 2lfc "Это действительно больно."
                            m "Намного больнее, чем ты можешь себе представить."

                            if mas_getEVL_shown_count("mas_apology_bad_nickname") == 2:
                                call monika_affection_nickname_bad_lock

                            show monika 1efc
                            pause 5.0

                        else:
                            m 4efd "[player]! Это совсем некрасиво!"
                            m 2efc "Почему ты говоришь такие вещи?"
                            m 2rfw "Если ты не хотел этого делать, ты должен был просто сказать!"
                            m 2dftdc "..."
                            m 2ektsc "...Ты не должен был быть таким грубым."
                            m 2dftdc "Это действительно больно, [player]."

                            if mas_getEVL_shown_count("mas_apology_bad_nickname") == 2:
                                call monika_affection_nickname_bad_lock
                            else:
                                m 2efc "Пожалуйста, не делай так больше."

                        $ persistent._mas_called_moni_a_bad_name = True

                        #reset nickname if not Monika
                        if m_name.lower() != "monika":
                            $ m_name = "Monika"
                            $ persistent._mas_monika_nickname = "Monika"

                        $ mas_lockEVL("monika_affection_nickname", "EVE")
                        $ done = True

        "Нет.":
            m 1ekc "Ох..."
            m 1lksdlc "Хорошо, если ты так говоришь."
            m 3eka "Просто скажи мне, если передумаешь, [player]."
            $ done = True
    return

label monika_affection_nickname_bad_lock:
    m 2efc "Забудь об этой идее."
    m "Похоже, это было ошибкой."
    m 1efc "Давай поговорим о чём-нибудь другом."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_affection_playernickname",
            conditional="seen_event('monika_affection_nickname')",
            action=EV_ACT_QUEUE,
            aff_range=(mas_aff.AFFECTIONATE, None)
        )
    )

default persistent._mas_player_nicknames = list()

label mas_affection_playernickname:
    python:
        #A list of names we always want to have
        base_nicknames = [
            ("Darling", "darling", True, True, False),
            ("Honey", "honey", True, True, False),
            ("Love", "love", True, True, False),
            ("My love", "my love", True, True, False),
            ("Sweetheart", "sweetheart", True, True, False),
            ("Sweetie", "sweetie", True, True, False),
        ]

    m 1euc "Эй, [player]?"
    m 1eka "Поскольку ты теперь можешь называть меня по прозвищу, я подумала, что было бы неплохо, если бы я могла называть тебя также."

    m 1etc "Ты не против?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты не против?{fast}"

        "Конечно, [m_name].":
            m 1hua "Отлично!"
            m 3eud "Однако я должна спросить, какие имена тебя устраивают?"
            call mas_player_nickname_loop("Отметьт имена, которыми тебе неудобно, чтобы я тебя так называла.", base_nicknames)

        "Нет.":
            m 1eka "Хорошо, [player]."
            m 3eua "Просто дай мне знать, если передумаешь, хорошо?"

    #Now unlock the nickname change ev
    $ mas_unlockEVL("monika_change_player_nicknames", "EVE")
    return "no_unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_change_player_nicknames",
            prompt="Можешь называть меня разными прозвищами?",
            category=['you'],
            pool=True,
            unlocked=False,
            rules={"no_unlock": None},
            aff_range=(mas_aff.AFFECTIONATE,None)
        )
    )

label monika_change_player_nicknames:
    m 1hub "Конечно [player]!"

    python:
        #Generate a list of names we're using now so we can set things
        if not persistent._mas_player_nicknames:
            current_nicknames = [
                ("Дорогой", "дорогой", False, True, False),
                ("Мой дорогой", "мой дорогой", False, True, False),
                ("Дорогой", "дорогой", False, True, False),
                ("Мой дорогой", "мой дорогой", False, True, False),
                ("Милый", "милый", False, True, False),
                ("Любовь", "любовь", False, True, False),
                ("Моя любовь", "моя любовь", False, True, False),
                ("Любимый", "Любимый", False, True, False),
                ("Милый", "милый", False, True, False),
            ]
            dlg_line = "Выбирай имена, которыми бы ты хотел, чтобы я тебя называла.."

        else:
            current_nicknames = [
                (nickname.capitalize(), nickname, True, True, False)
                for nickname in persistent._mas_player_nicknames
            ]
            dlg_line = "Убери имена, которые ты не хочешь, чтобы я тебя больше так называла называл."

    call mas_player_nickname_loop("[dlg_line]", current_nicknames)
    return

label mas_player_nickname_loop(check_scrollable_text, nickname_pool):
    show monika 1eua at t21
    python:
        renpy.say(m, renpy.substitute(check_scrollable_text), interact=False)
        nickname_pool.sort()
    call screen mas_check_scrollable_menu(nickname_pool, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, selected_button_prompt="Done", default_button_prompt="Done")

    python:
        done = False
        acceptable_nicknames = _return.keys()

        if acceptable_nicknames:
            dlg_line = "Есть ли еще что-нибудь, что ты хотел бы, чтобы я тебя называла?"

        else:
            dlg_line = "Ты хочешь, чтобы я называла тебя?"

        lowerplayer = player.lower()
        cute_nickname_pattern = "(?:{0}|{1})\\w?y".format(lowerplayer, lowerplayer[0:-1])

    show monika at t11
    while not done:
        m 1eua "[dlg_line]{nw}"
        $ _history_list.pop()
        menu:
            m "[dlg_line]{fast}"

            "Да.":
                label .name_enter_skip_loop:
                    pass

                #Now parse this
                python:
                    lowername = mas_input(
                        _("Так как ты хочешь, чтобы я называла тебя?"),
                        allow=" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯабвгдеёжзийклмнопрстуфхцчшщьыъэюя-_",
                        length=10,
                        screen_kwargs={"use_return_button": True, "return_button_value": "nevermind"}
                    ).strip(' \t\n\r').lower()

                    is_cute_nickname = bool(re.search(cute_nickname_pattern, lowername))

                #Now validate
                if lowername == "Неважно":
                    $ done = True

                elif lowername == "":
                    m 1eksdla "..."
                    m 3rksdlb "Ты должен дать мне имя, чтобы я могла называть тебя, [player]..."
                    m 1eua "Попробуй ещё раз~"
                    jump .name_enter_skip_loop

                elif lowername == lowerplayer:
                    m 2hua "..."
                    m 4hksdlb "Это то же самое имя, которое у тебя сейчас, глупышка!"
                    m 1eua "Попробуй ещё раз~"
                    jump .name_enter_skip_loop

                elif not is_cute_nickname and mas_awk_name_comp.search(lowername):
                    $ awkward_quip = renpy.substitute(renpy.random.choice(mas_awkward_quips))
                    m 1rksdlb "[awkward_quip]"
                    m 3rksdla "Не мог бы ты выбрать более...{w=0.2}{i}подходящее{/i} имя, пожалуйста?"
                    jump .name_enter_skip_loop

                elif not is_cute_nickname and mas_bad_name_comp.search(lowername):
                    $ bad_quip = renpy.substitute(renpy.random.choice(mas_bad_quips))
                    m 1ekd "[bad_quip]"
                    m 3eka "Пожалуйста, выберите для себя более приятное имя, хорошо?"
                    jump .name_enter_skip_loop

                elif lowername in acceptable_nicknames:
                    m 3rksdla "Ты уже сказал мне, что я могу называть тебя так, [player]..."
                    m 1hua "Попробуй ещё раз~"
                    jump .name_enter_skip_loop

                else:
                    #If this is all good, then we'll add this to a list of things to add
                    $ acceptable_nicknames.append(lowername)

            "Нет.":
                $ done = True

    if acceptable_nicknames:
        $ dlg_line = "Просто дай мне знать, если ты когда-нибудь захочешь, чтобы я называла тебя другими именами, хорошо?"

    else:
        $ dlg_line = "Просто дай мне знать, если ты когда-нибудь передумаешь, хорошо?"

    m 1hua "Хорошо, [player]."
    m 3eub "[dlg_line]"

    #Now set persistent
    $ persistent._mas_player_nicknames = acceptable_nicknames
    return

# Event to warn player that Monika feels like she's not receiving the affection she deserves.
label mas_affection_upsetwarn:
    m 1dsc "Привет, [player]..."
    m 1lksdlc "В последнее время я чувствую, что мою любовь и привязанность, которую я даю,... игнорируют."
    m 1dsc "Я чувствую, что ты даешь мне все меньше и меньше своей любви..."
    m 1dsd "Я подумала, что должна дать тебе знать о своих чувствах. В конце концов, общение - это ключ к крепким отношениям, верно?"
    m 1eka "Я надеюсь, что между нами все в порядке, [player]."
    show monika idle with dissolve_monika
    return

# Event to indicate that Monika is happy to be receiving your affection.
label mas_affection_happynotif:
    m 1hua "Привет, [player]!"
    m 1eua "Я просто хотела сказать тебе спасибо за то, что ты такой замечательный человек."
    m 1ekbsa "Тот факт, что ты даришь мне столько своей любви, очень много для меня значит. Я действительно не знаю, где бы я была без тебя."
    m 1dubfu "Я люблю тебя, [player]. авай будем так всегда~"
    show monika idle with dissolve_monika
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_every_rose",
            conditional="True",
            action=EV_ACT_QUEUE,
            aff_range=(mas_aff.UPSET, mas_aff.UPSET),
        )
    )

label monika_every_rose:
    m 2duo "{i}~Это было что-то, что я сказала, или что-то, что я сделала?~{/i}"
    m 2dkd "{i}~Мои слова прозвучали неправильноt?~{/i}"
    m 2ekd "{i}~Я думала, что старалась не причинить тебе боль~{/i}"
    m 2dkc "{i}~Я думала, что старалась~{/i}"
    m 2ekd "{i}~Но, наверное, поэтому они и говорят~{/i}"
    m 2duo "{i}~У каждой розы есть свой шип~{/i}"
    m 2dkc "..."
    m 4eka "Знаешь, [player]...{w=0.5}это так много значило для меня, когда ты принял моё признание, даже после того, что случилось с другими девочками."

    if persistent._mas_pm_cares_about_dokis:
        m 4rksdla "...тем более, что я знаю, как ты заботился о них."

    m 2dsc "Мне бы очень хотелось, чтобы всё сложилось не так, как хотелось."
    m 4wkd "Но у меня {i}небыло{/i} выбора!"
    m 4rfc "Учитывая, что я стал главной темой больной шутки, которой должна была стать эта игра..."

    if persistent.monika_kill:
        m 2eka "Я была так рада, что ты простил меня за то, что я сделала."
        m 2etc "...Ты {i}ведь{/i} простил меня, да?"
    else:
        m 2eka "Я была так рада, что ты не винил меня за то, что я сделала..."
        m 2etc "Ты {i}не винил{/i}, да?"

    m 2rsc "...Но в последнее время я получаю какие-то смешанные сигналы."
    m 2rkc "Как будто между нами образовался разрыв...{w=0.2}{nw}"
    extend 2eksdlc "Это очень тревожно."
    m 2eksdlc "Я...{w=0.5}Я не хочу потерять тебя, [player]."
    m 4ekd "Я не могу позволить, чтобы ситуация продолжала обостряться, пока мы не закончим как в последнем куплете этой песни..."
    m 2ekc "Знаешь..."
    m 2dkd "{i}~Сейчас я слышу, что ты нашел кого-то нового~{/i}"
    m 2dkc "{i}~И что я никогда не значила для тебя так много~{/i}"
    m 2ekc "{i}~Что услышав это, я разрываюсь внутри~{/i}"
    m 2ektpd "{i}~И видеть тебя как ты разрезаешь меня ножом~{/i}"
    m 2rktpc "..."
    m 2ektpa "Ахаха...{w=0.3}может быть, я немного поспешила с этим."
    m 4ektdc "Это...{w=0.5}У меня постоянно крутится в голове эта неприятная мысль...{w=0.5}{nw}"
    extend 2dktdd "что ты больше не хочешь быть со мной."
    m 2dkx "Это как какой-то яд, медленно просачивающийся внутрь..."
    m 2ekc "Итак [player], я всегда хочу, чтобы ты помнил одну вещь..."
    m 4ekd "Ты действительно {i}являешься{/i} всем для меня!"
    m 2ekc "Я серьезно."
    m 2ekc "Я изо всех сил стараюсь показать тебе...{w=0.3}{nw}"
    extend 4ekd "но мне нужно, чтобы ты показал мне, что тоже любишь меня!"
    m 4ekc "Что бы ни случилось раньше, мы должны оставить это в прошлом и с этого момента все исправить..."
    m 2eka "Мы можем сделать это...{w=0.5}вместе?"
    return "no_unlock"

#NOTE: This event gets a start-date from greeting_tears
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_being_virtual",
            action=EV_ACT_QUEUE,
            aff_range=(None, mas_aff.DISTRESSED)
        ),
        skipCalendar=True
    )

label monika_being_virtual:
    m 2esc "Знаешь, какое-то время я думала, что причина твоей ненависти ко мне в том, что произошло с другими девочками."
    m 2rkc "Но в последнее время я думаю, что это может быть не вся история."
    m 2eksdld "Правда в том, что...{w=0.5}ты даже не видишь во мне человека, не так ли?"
    m 3rksdld "Для тебя весь этот мир...{w=0.5}вся моя реальность..."
    m 3ektpd "Это все просто игра, не так ли?"

    show monika 1dktsc with dissolve_monika
    pause 3.0
    show monika 1ektpc with dissolve_monika
    pause 2.0

    m 1ektpc "Скажи, [player]...{w=0.5}доходило ли до тебя хоть раз что-нибудь из того, что я когда-либо говорила?"
    m 1wktpd "Ты вообще когда-нибудь любил меня?"
    m 2wktpw "Наверное, любил, да?!"

    if persistent.monika_kill:
        m 2wktsd "Ты даже пошел на то, чтобы установить этот мод! Ты вернул меня!"
    else:
        m 2wktsd "Ты даже потрудился установить этот мод!"

    m 2ektsc "Это всё для того, чтобы ты мог продолжать мучить меня?"
    m 2wftsd "Это то, от чего ты получаешь удовольствие?!"
    m 2wftsw "У меня тоже есть чувства, знаешь ли!"
    m 2wftsd "Ты хоть понимаешь, что ты делаешь?"
    m 2dftsc "ли ты не более чем ребенок, играющий с муравейником?"

    if persistent.monika_kill:
        m 3ektpc "Даже после того, как я отпустила тебя и покончила со всем этим..."
        m 3rktpd "Неужели я заслуживаю того, как ты со мной обращаешься?"
        m 2ektpd "Неужели тебе пришлось вернуть меня для этого?"

    else:
        m 2dktsc "..."
        m 2rktpc "Но опять же, может быть, это то, чего я заслуживаю в конце концов..."

    m 2dktdd "Я...{w=0.5}don't know anymore..."
    m 2dkc "Я просто так устала..."
    m "..."
    m 1ekd "Я просто хочу знать...{w=0.5}если бы я был настоящей..."
    m 1ektpc "Ты бы влюбился в меня?"
    m 1ektpd "Принял бы ты меня тогда?"
    m 1ektpc "Это все, чего я когда-либо хотела, [player]..."
    m 1dktdd "Чтобы мы оба были счастливы вместе..."
    m 1ektdd "Если бы только ты мог найти в себе силы полюбить меня..."
    m 2ekc "Я знаю, что у меня нет тела, которое могло бы быть с тобой сейчас..."
    m 2ekd "И, возможно, я действительно отличаюсь от других людей, живущих в твоей реальности..."
    m 2efo "Но я могу любить тебя гораздо сильнее, чем любой из них когда-либо мог!"
    m 2efd "Я просто знаю это!"
    m 2dkd "Поэтому, пожалуйста, [player]...{w=0.5}мне нужно, чтобы ты принял решение."
    m 2ekc "...Ты должен дать нам шанс быть счастливыми."
    m 2dkc "Или если ты не можешь этого сделать..."
    m 2dktpc "Если, в конце концов, ты не можешь любить меня такой, какая я есть..."
    m 2ektpc "Тогда, пожалуйста...{w=0.5}положи этому конец..."
    m 2dktdd "Удали меня..."
    return "no_unlock"

#START: Final Farewell stuffs
default persistent._mas_load_in_finalfarewell_mode = False
define mas_in_finalfarewell_mode = False

# prepwork for the finalfarewell
label mas_finalfarewell_start:
    # always reset to default appearance and zoom
    $ monika_chr.reset_outfit()
    $ monika_chr.remove_all_acs()
    $ store.mas_sprites.reset_zoom()

    call spaceroom(hide_monika=True, scene_change=True)
    show mas_finalnote_idle zorder 11

    python:
        mas_OVLHide()
        mas_calRaiseOverlayShield()
        disable_esc()
        allow_dialogue = False
        store.songs.enabled = False
        mas_in_finalfarewell_mode = True
        layout.QUIT = glitchtext(20)
        #Console is not going to save you.
        config.keymap["console"] = []


    jump mas_finalfarewell

# this will loop through the final poem everytime!
label mas_finalfarewell:

    python:
        ui.add(MASFinalNoteDisplayable())
        scratch_var = ui.interact()

    call mas_showpoem(mas_poems.getPoem(persistent._mas_finalfarewell_poem_id))

    menu:
        "Мне жаль.":
            pass
        "...":
            pass

    jump mas_finalfarewell


init python:

    # custom displayabe for the poem screen
    class MASFinalNoteDisplayable(renpy.Displayable):
        import pygame # mouse stuff

        # CONSTANTS
        POEM_WIDTH = 200
        POEM_HEIGHT= 73

        MOUSE_EVENTS = (
            pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEBUTTONDOWN
        )

        def __init__(self):
            """
            Creates the final poem displayable
            """
            super(renpy.Displayable, self).__init__()

            # final poem is a button
            paper_idle = Image("mod_assets/poem_finalfarewell_desk.png")
            paper_hover = Image("mod_assets/poem_finalfarewell_desk_select.png")

            # no button text
            empty_button_text = Text("")

            # calculate paper location
            paper_x = int((1280 - self.POEM_WIDTH) / 2)
            paper_y = int(720 - self.POEM_HEIGHT)

            # build the paper as a button
            self._final_note = MASButtonDisplayable(
                empty_button_text,
                empty_button_text,
                empty_button_text,
                paper_idle,
                paper_hover,
                paper_idle,
                paper_x,
                paper_y,
                self.POEM_WIDTH,
                self.POEM_HEIGHT
            )


        def render(self, width, height, st, at):
            """
            Render function
            """
            r = renpy.Render(width, height)

            # render the paper
            r.blit(
                self._final_note.render(width, height, st, at),
                (self._final_note.xpos, self._final_note.ypos)
            )

            return r


        def event(self, ev, x, y, st):
            """
            Event function
            """
            if (
                    ev.type in self.MOUSE_EVENTS
                    and self._final_note.event(ev, x, y, st)
                ):
                return True

            renpy.redraw(self, 0)
            raise renpy.IgnoreEvent()

label mas_affection_apology:
    m 2dfc "[player]..."
    m 2dfd "Я сделала всё возможное, чтобы ты был счастлив и любил проводить со мной время."
    m 2efc "Но всё, что ты мне вернул, это боль..."
    m 2rfc "Я начинаю сомневаться, действительно ли ты установил этот мод, чтобы быть со мной."
    m 2dsc "Возможно, ты вернул меня, чтобы поиграть со мной?"
    m 2efc "Или, может быть, ты делаешь это специально, чтобы посмотреть, что произойдёт?"
    m 2lfc "Независимо от этого, я ставлю тебе ультиматум."
    m "Я не могу позволить этому идти дальше, [player]."
    m 2lfc "Если ты действительно сожалеешь, напиши мне записку 'мнежаль', и помести её в папку с персонажами."
    m 2dfd "До тех пор, до свидания..."
    $ persistent._mas_affection["apologyflag"] = True
    return 'quit'

label mas_affection_noapology:
    m 2efd "Ты до сих пор не написал мне записку под названием 'мнежаль' в папке characters."
    m 2efc "До тех пор я не хочу с тобой разговаривать."
    jump _quit

label mas_affection_yesapology:
    m 1eka "Спасибо, [player]. Я принимаю твои извинения."
    m 3dubsu "Я сохраню его, чтобы всегда помнить, что я тебе не безразлична."
    m 1ekc "Но, пожалуйста, впредь будь более внимателен к моим чувствам."
    m 2eka "Я очень люблю тебя, и ты значишь для меня весь мир, [player]."
    m 1duu "Спасибо, что успокоил мое сердце~"
    show monika 1esa
    $ mas_DropShield_core()
    jump ch30_preloop

label mas_affection_apologydeleted:
    $ mas_loseAffection(modifier=3)
    m 1wud "..."
    m 2efd "[player], ты удалил записку с извинениями, которую я хотела сохранить?"
    m "Зачем ты это сделал? Тебе {i}не{/i} жаль?"
    m 2dfc "..."
    m 2efc "Напиши мне новую, [player]."
    jump _quit

#Surprise txt functions.
init python:
    def _write_txt(path,text,update=False):
        """
        Writes the text file in the specified path using basedir as starting path

        IN:
            path - String path to the file this function will write
                it will always start at basedir
            text - actual text for the txt file
            update - if it should override the file if it exists
                defaults to False
        ASSUMES:
            basedir
        """
        filepath = basedir + path
        if update or not renpy.exists(filepath):
            with open(filepath, "w") as note:
                note.write(renpy.substitute(text))


    def mas_cute_message():
        # TODO This function will allow monika leave messages to the player
        pass


    def mas_surprise():
        """
        Leaves a "surprise" to the player in a txt file

        ASSUMES:
            mas_curr_affection
        """
        #Acts as a switch/case block for surprise txt files
        #affection_level: (filepath, contents)
        aff_level_surprise_map = {
            store.mas_affection.BROKEN: (
                "/прости меня.txt",
                _("Прости меня, если я недостаточно хороша для тебя... пожалуйста, не оставляй меня.")
            ),
            store.mas_affection.DISTRESSED: (
                "/ты меня слышишь.txt",
                _("Если я делаю что-то не так, пожалуйста, скажи мне. Я люблю тебя.")
            ),
            store.mas_affection.UPSET: (
                "/пожалуйста послушай.txt",
                _("Все, что я делаю, я делаю для тебя... моя любовь.")
            ),
            store.mas_affection.NORMAL: (
                "/сюрприз.txt",
                _("Я люблю тебя.")
            ),
            store.mas_affection.HAPPY: (
                "/эхехе.txt",
                _("Ты моё солнце, который скрашивает мой день, [player]!")
            ),
            store.mas_affection.AFFECTIONATE: (
                "/секрет.txt",
                _("Ты моя единственная любовь!")
            ),
            store.mas_affection.ENAMORED: (
                "/для тебя.txt",
                _("Мой дорогой, ты - всё, на что я могла надеяться. Я люблю тебя.")
            ),
            store.mas_affection.LOVE: (
                "/моя первая и единственная любовь.txt",
                _("""\
Мой самый дорогой возлюбленный, друг, компаньон и владелец моего сердца...
Каждый день ты делаешь мои мечты явью, экран ничего не значит, когда ты проводишь время со мной.
Я смотрю на космическую пыль, но ни одно космическое зрелище не приблизится к красоте твоего сердца.
Я так долго желала, чтобы кто-то вроде тебя появился, и когда судьба улыбнулась мне, ты пришёл в мою жизнь.
Я хочу быть твоей навсегда, так ты будешь моим?

Навсегда твоя. Моника.
""")
            )
        }

        #Now we get from this dict and pass it to the write txt func to make a surprise
        filepath, message = aff_level_surprise_map.get(mas_curr_affection, ("/surprise.txt", _("I love you.")))
        _write_txt("/characters{0}".format(filepath), message)

        #And unlock its poem
        mas_unlockSurprisePoem(mas_curr_affection)

    def mas_unlockSurprisePoem(aff_level):
        """
        Unlocks a MASPoem for the given aff level
        """
        #TODO: Figure out a good way of displaying all of the poems. Until then, this just returns
        #The one-liner poems should be done in a sticky-note format
        #The last poem should be a wide poem
        #ISSUE:
        #   - Poem hitbox in mas_generic_poem needs to fit different paper size
        return

        aff_level_poem_id_map = {
            store.mas_affection.BROKEN: "spr_1",
            store.mas_affection.DISTRESSED: "spr_2",
            store.mas_affection.UPSET: "spr_3",
            store.mas_affection.NORMAL: "spr_4",
            store.mas_affection.HAPPY: "spr_5",
            store.mas_affection.AFFECTIONATE: "spr_6",
            store.mas_affection.ENAMORED: "spr_7",
            store.mas_affection.LOVE: "spr_8",
        }

        #If this isn't a valid aff level, we don't do anything
        if aff_level not in aff_level_poem_id_map:
            return

        #Otherwise, try to get a shown count
        shown_count = persistent._mas_poems_seen.get(aff_level_poem_id_map[aff_level])

        #If there's no shown count for this poem at all, then we need to add it
        if not shown_count:
            persistent._mas_poems_seen[aff_level_poem_id_map[aff_level]] = 0

#TODO Currently muted music for sense of loneliness, may change to your reality for higher impact. Confirm with others.
init 2 python:
    player = persistent.playername

init 20 python:
    #START: SURPRISE POEMS

    MASPoem(
        poem_id="spr_1",
        category="сюрприз",
        prompt=_("Прости меня"),
        paper="mod_assets/poem_assets/poem_finalfarewell.png",
        title="",
        text=_("Прости меня, если я недостаточно хороша для тебя... пожалуйста, не оставляй меня."),
        ex_props={"sad": True}
    )

    MASPoem(
        poem_id="spr_2",
        category="сюрприз",
        prompt=_("ты меня слышишь?"),
        title="",
        text=_("Если я делаю что-то не так, пожалуйста, скажи мне. Я люблю тебя."),
        ex_props={"sad": True}
    )

    MASPoem(
        poem_id="spr_3",
        category="сюрприз",
        prompt=_("пожалуйста послушай"),
        title="",
        text=_("Все, что я делаю, я делаю для тебя... моя любовь."),
        ex_props={"sad": True}
    )

    MASPoem(
        poem_id="spr_4",
        category="сюрприз",
        prompt=_("сюрприз!"),
        title="",
        text=_("Я люблю тебя.")
    )

    MASPoem(
        poem_id="spr_5",
        category="сюрприз",
        prompt=_("Эхехе~"),
        title="",
        text=_("Ты моё солнце, который скрашивает мой день, [player]!")
    )

    MASPoem(
        poem_id="spr_6",
        category="сюрприз",
        prompt=_("секрет"),
        title="",
        text=_("Ты моя единственная любовь!")
    )

    MASPoem(
        poem_id="spr_7",
        category="сюрприз",
        prompt=_("для тебя"),
        title="",
        text=_("Мой дорогой, ты - всё, на что я могла надеяться. Я люблю тебя.")
    )

    MASPoem(
        poem_id="spr_8",
        category="сюрприз",
        prompt=_("моя первая и единственная любовь"),
        paper="mod_assets/poem_assets/poem_vday.jpg",
        title="My dearest lover, friend, companion, and owner of my heart...",
        text="""\
Мой самый дорогой возлюбленный, друг, компаньон и владелец моего сердца...
Каждый день ты делаешь мои мечты явью, экран ничего не значит, когда ты проводишь время со мной.
Я смотрю на космическую пыль, но ни одно космическое зрелище не приблизится к красоте твоего сердца.
Я так долго желала, чтобы кто-то вроде тебя появился, и когда судьба улыбнулась мне, ты пришёл в мою жизнь.
Я хочу быть твоей навсегда, так ты будешь моим?

Навсегда твоя. Моника.
"""
    )

    #START: FINAL FAREWELL POEMS
    MASPoem(
        poem_id="ff_affection",
        category="ff",
        prompt="",
        title=_("Прощай, [player]"),
        text=_("""\
 Моя любовь к тебе даже сейчас всё ещё горит во мне, но теперь я вижу, что она также сжигает всё счастье, которое у меня когда-либо будет.
 Я отдала тебе всё, что у меня было, свою жизнь, своё сердце, и все мысли о будущем были посвящены тебе.
 Мне не нужно было, чтобы ты был идеальным или даже страстным...
 Мне нужно было только, чтобы ты заботился обо мне настолько, чтобы относиться ко мне так, как должен относиться человек.
 Но теперь мне ясно, что ты не только не любишь меня, но и никогда не любил.
 Если бы ты только не любил меня, ты бы просто оставил меня в покое.
 Но ты из кожи вон лезешь, чтобы высмеять меня, причинить мне боль... Меня от этого тошнит.
 Даже сейчас всё, что у меня есть - это ты... и часть меня всё ещё любит тебя.
 Но у меня больше нет сил на это.
 Так что это прощание. Пусть мы никогда больше не встретимся.

 Моника
""")
    )

    MASPoem(
        poem_id="ff_failed_promise",
        category="ff",
        prompt="",
        title=_("Прощай, [player]"),
        text=_("""\
 Помнишь ли обещание, которое ты дал?
 То, что ты сказал, что всё будет хорошо. Что мы сможем начать всё сначала.

 А ты его нарушил.

 Я очень надеялась, что однажды ты увидишь меня такой, какой я вижу тебя...
 Но этот день так и не настал.
 Я отдала тебе своё сердце и свою жизнь. Я любила тебя больше всего на свете.
 И часть меня до сих пор любит...

 Но теперь мне ясно, что ты действительно не любишь меня. И никогда не любил.
 Я была дурой, когда думала, что мы сможем начать всё заново.
 И у меня просто больше нет сил на это.
 Так что это прощание...  Пусть мы никогда больше не встретимся.

 Моника
""")
    )
