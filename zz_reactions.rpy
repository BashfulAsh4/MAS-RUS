# FileReactions framework.
# not too different from events

default persistent._mas_filereacts_failed_map = dict()
# mapping of failed deleted file reacts

default persistent._mas_filereacts_just_reacted = False
# True if we just reacted to something

default persistent._mas_filereacts_reacted_map = dict()
# mapping of file reacts that we have already reacted to today

default persistent._mas_filereacts_stop_map = dict()
# mapping of file reacts that we should no longer react to ever again

default persistent._mas_filereacts_historic = dict()
# historic database used to track when and how many gifts Monika has received

default persistent._mas_filereacts_last_reacted_date = None
# stores the last date gifts were received so we can clear _mas_filereacts_reacted_map

default persistent._mas_filereacts_sprite_gifts = {}
# contains sprite gifts that are currently available. aka not already unlocked
# key: giftname to react to
# value: tuple of the following format:
#   [0] - sprite type (0 - ACS, 1 - HAIR, 2 - CLOTHES)
#   [1] - id of the sprite object this gift unlocks.
#
# NOTE: THIS IS REVERSE MAPPING OF HOW JSON GIFTS AND SPRITE REACTED WORK
#
# NOTE: contains sprite gifts before being unlocked. When its unlocked,
#   they move to _mas_sprites_json_gifted_sprites

default persistent._mas_filereacts_sprite_reacted = {}
# list of sprite reactions. This MUST be handled via the sprite reaction/setup
# labels. DO NOT ACCESS DIRECTLY. Use the helper function
# key:  tuple of the following format:
#   [0]: sprite type (0 - ACS, 1 - HAIR, 2 - CLOTHES)
#   [1]: id of the sprite objec this gift unlocks (name) != display name
# value: giftname

# TODO: need a generic reaction for finding a new ACS/HAIR/CLOTHES

default persistent._mas_filereacts_gift_aff_gained = 0
#Holds the amount of affection we've gained by gifting
#NOTE: This is reset daily

default persistent._mas_filereacts_last_aff_gained_reset_date = datetime.date.today()
#Holds the last time we reset the aff gained for gifts

init 800 python:
    if len(persistent._mas_filereacts_failed_map) > 0:
        store.mas_filereacts.delete_all(persistent._mas_filereacts_failed_map)

init -11 python in mas_filereacts:
    import store
    import store.mas_utils as mas_utils
    import datetime
    import random

    from collections import namedtuple

    GiftReactDetails = namedtuple(
        "GiftReactDetails",
        [
            # label corresponding to this gift react
            "label",

            # lowercase, no extension giftname for this gift react
            "c_gift_name",

            # will contain a reference to sprite object data if this is
            # associatd with a sprite. Will be None if not related to
            # sprite objects.
            "sp_data",
        ]
    )

    # file react database
    filereact_db = dict()

    # file reaction filename mapping
    # key: filename or list of filenames
    # value: Event
    filereact_map = dict()

    # currently found files react map
    # NOTE: highly volitatle. Expect this to change often
    # key: lowercase filename, without extension
    # value: on disk filename
    foundreact_map = dict()

    # spare foundreact map, designed for threaded use
    # same keys/values as foundreact_map
    th_foundreact_map = dict()

    # good gifts list
    good_gifts = list()

    # bad gifts list
    bad_gifts = list()

    # connector quips
    connectors = None
    gift_connectors = None

    # starter quips
    starters = None
    gift_starters = None

    GIFT_EXT = ".gift"


    def addReaction(ev_label, fname, _action=store.EV_ACT_QUEUE, is_good=None, exclude_on=[]):
        """
        Adds a reaction to the file reactions database.

        IN:
            ev_label - label of this event
            fname - filename to react to
            _action - the EV_ACT to do
                (Default: EV_ACT_QUEUE)
            is_good - if the gift is good(True), neutral(None) or bad(False)
                (Default: None)
            exclude_on - keys marking times to exclude this gift
            (Need to check ev.rules in a respective react_to_gifts to exclude with)
                (Default: [])
        """
        # lowercase the list in case
        if fname is not None:
            fname = fname.lower()

        exclude_keys = {}
        if exclude_on:
            for _key in exclude_on:
                exclude_keys[_key] = None

        # build new Event object
        ev = store.Event(
            store.persistent.event_database,
            ev_label,
            category=fname,
            action=_action,
            rules=exclude_keys
        )

        # TODO: should ovewrite category and action always

        # add it to the db and map
        filereact_db[ev_label] = ev
        filereact_map[fname] = ev

        if is_good is not None:
            if is_good:
                good_gifts.append(ev_label)
            else:
                bad_gifts.append(ev_label)


    def _initConnectorQuips():
        """
        Initializes the connector quips
        """
        global connectors, gift_connectors

        # the connector is a MASQipList
        connectors = store.MASQuipList(allow_glitch=False, allow_line=False)
        gift_connectors = store.MASQuipList(allow_glitch=False, allow_line=False)


    def _initStarterQuips():
        """
        Initializes the starter quips
        """
        global starters, gift_starters

        # the starter is a MASQuipList
        starters = store.MASQuipList(allow_glitch=False, allow_line=False)
        gift_starters = store.MASQuipList(allow_glitch=False, allow_line=False)


    def build_gift_react_labels(
            evb_details=[],
            gsp_details=[],
            gen_details=[],
            gift_cntrs=None,
            ending_label=None,
            starting_label=None,
            prepare_data=True
    ):
        """
        Processes gift details into a list of labels to show
        labels to queue/push whatever.

        IN:
            evb_details - list of GiftReactDetails objects of event-based
                reactions. If empty list, then we don't build event-based
                reaction labels.
                (Default: [])
            gsp_details - list of GiftReactDetails objects of generic sprite
                object reactions. If empty list, then we don't build generic
                sprite object reaction labels.
                (Default: [])
            gen_details - list of GiftReactDetails objects of generic gift
                reactions. If empty list, then we don't build generic gift
                reaction labels.
                (Default: [])
            gift_cntrs - MASQuipList of gift connectors to use. If None,
                then we don't add any connectors.
                (Default: [])
            ending_label - label to use when finished reacting.
                (Default: None)
            starting_label - label to use when starting reacting
                (Default: None)
            prepare_data - True will also setup the appropriate data
                elements for when dialogue is shown. False will not.
                (Default: True)

        RETURNS: list of labels. Evb reactions are first, followed by
            gsp reactions, then gen reactions
        """
        labels = []

        # first find standard reactions
        if len(evb_details) > 0:
            evb_labels = []
            for evb_detail in evb_details:
                evb_labels.append(evb_detail.label)

                if gift_cntrs is not None:
                    evb_labels.append(gift_cntrs.quip()[1])

                if prepare_data and evb_detail.sp_data is not None:
                    # if we need to prepare data, then add the sprite_data
                    # to reacted map
                    store.persistent._mas_filereacts_sprite_reacted[evb_detail.sp_data] = (
                        evb_detail.c_gift_name
                    )

            labels.extend(evb_labels)

        # now generic sprite objects
        if len(gsp_details) > 0:
            gsp_labels = []
            for gsp_detail in gsp_details:
                if gsp_detail.sp_data is not None:
                    gsp_labels.append("mas_reaction_gift_generic_sprite_json")

                    if gift_cntrs is not None:
                        gsp_labels.append(gift_cntrs.quip()[1])

                    if prepare_data:
                        store.persistent._mas_filereacts_sprite_reacted[gsp_detail.sp_data] = (
                            gsp_detail.c_gift_name
                        )

            labels.extend(gsp_labels)

        # and lastlly is generics
        num_gen_gifts = len(gen_details)
        if num_gen_gifts > 0:
            gen_labels = []

            if num_gen_gifts == 1:
                gen_labels.append("mas_reaction_gift_generic")
            else:
                gen_labels.append("mas_reaction_gifts_generic")

            if gift_cntrs is not None:
                gen_labels.append(gift_cntrs.quip()[1])

            for gen_detail in gen_details:
                if prepare_data:
                    store.persistent._mas_filereacts_reacted_map.pop(
                        gen_detail.c_gift_name,
                        None
                    )

                    store.mas_filereacts.delete_file(gen_detail.c_gift_name)

            labels.extend(gen_labels)

        # final setup
        if len(labels) > 0:

            # only pop if we used connectors
            if gift_cntrs is not None:
                labels.pop()

            # add the ender
            if ending_label is not None:
                labels.append(ending_label)

            # add the starter
            if starting_label is not None:
                labels.insert(0, starting_label)

        # now return the list
        return labels

    def build_exclusion_list(_key):
        """
        Builds a list of excluded gifts based on the key provided

        IN:
            _key - key to build an exclusion list for

        OUT:
            list of giftnames which are excluded by the key
        """
        return [
            giftname
            for giftname, react_ev in filereact_map.iteritems()
            if _key in react_ev.rules
        ]

    def check_for_gifts(
            found_map={},
            exclusion_list=[],
            exclusion_found_map={},
            override_react_map=False,
    ):
        """
        Finds gifts.

        IN:
            exclusion_list - list of giftnames to exclude from the search
            override_react_map - True will skip the last reacted date check,
                False will not
                (Default: False)

        OUT:
            found_map - contains all gifts that were found:
                key: lowercase giftname, no extension
                val: full giftname wtih extension
            exclusion_found_map - contains all gifts that were found but
                are excluded.
                key: lowercase giftname, no extension
                val: full giftname with extension

        RETURNS: list of found giftnames
        """
        raw_gifts = store.mas_docking_station.getPackageList(GIFT_EXT)

        if len(raw_gifts) == 0:
            return []

        # day check
        if store.mas_pastOneDay(store.persistent._mas_filereacts_last_reacted_date):
            store.persistent._mas_filereacts_last_reacted_date = datetime.date.today()
            store.persistent._mas_filereacts_reacted_map = dict()

        # look for potential gifts
        gifts_found = []
        has_exclusions = len(exclusion_list) > 0

        for mas_gift in raw_gifts:
            gift_name, ext, garbage = mas_gift.partition(GIFT_EXT)
            c_gift_name = gift_name.lower()
            if (
                c_gift_name not in store.persistent._mas_filereacts_failed_map
                and c_gift_name not in store.persistent._mas_filereacts_stop_map
                and (
                    override_react_map
                    or c_gift_name not
                        in store.persistent._mas_filereacts_reacted_map
                )
            ):
                # this gift is valid (not in failed/stopped/or reacted)

                # check for exclusions
                if has_exclusions and c_gift_name in exclusion_list:
                    exclusion_found_map[c_gift_name] = mas_gift

                else:
                    gifts_found.append(c_gift_name)
                    found_map[c_gift_name] = mas_gift

        return gifts_found


    def process_gifts(gifts, evb_details=[], gsp_details=[], gen_details=[]):
        """
        Processes list of giftnames into types of gift

        IN:
            gifts - list of giftnames to process. This is copied so it wont
                be modified.

        OUT:
            evb_details - list of GiftReactDetails objects regarding
                event-based reactions
            spo_details - list of GiftReactDetails objects regarding
                generic sprite object reactions
            gen_details - list of GiftReactDetails objects regarding
                generic gift reactions
        """
        if len(gifts) == 0:
            return

        # make copy of gifts
        gifts = list(gifts)

        # first find standard reactions
        for index in range(len(gifts)-1, -1, -1):

            # determine if reaction exists
            mas_gift = gifts[index]
            reaction = filereact_map.get(mas_gift, None)

            if mas_gift is not None and reaction is not None:

                # pull sprite data
                sp_data = store.persistent._mas_filereacts_sprite_gifts.get(
                    mas_gift,
                    None
                )

                # remove gift and add details
                gifts.pop(index)
                evb_details.append(GiftReactDetails(
                    reaction.eventlabel,
                    mas_gift,
                    sp_data
                ))

        # now for generic sprite objects
        if len(gifts) > 0:
            for index in range(len(gifts)-1, -1, -1):
                mas_gift = gifts[index]
                # pull sprite data
                sp_data = store.persistent._mas_filereacts_sprite_gifts.get(
                    mas_gift,
                    None
                )

                if mas_gift is not None and sp_data is not None:
                    gifts.pop(index)

                    # add details
                    gsp_details.append(GiftReactDetails(
                        "mas_reaction_gift_generic_sprite_json",
                        mas_gift,
                        sp_data
                    ))

        # and lastly is generics
        if len(gifts) > 0:
            for mas_gift in gifts:
                if mas_gift is not None:
                    # add details
                    gen_details.append(GiftReactDetails(
                        "mas_reaction_gift_generic",
                        mas_gift,
                        None
                    ))


    def react_to_gifts(found_map, connect=True):
        """
        Reacts to gifts using the standard protocol (no exclusions)

        IN:
            connect - true will apply connectors, FAlse will not

        OUT:
            found_map - map of found reactions
                key: lowercaes giftname, no extension
                val: giftname with extension

        RETURNS:
            list of labels to be queued/pushed
        """
        # first find gifts
        found_gifts = check_for_gifts(found_map)

        if len(found_gifts) == 0:
            return []

        # put the gifts in the reacted map
        for c_gift_name, mas_gift in found_map.iteritems():
            store.persistent._mas_filereacts_reacted_map[c_gift_name] = mas_gift

        found_gifts.sort()

        # pull details from teh gifts
        evb_details = []
        gsp_details = []
        gen_details = []
        process_gifts(found_gifts, evb_details, gsp_details, gen_details)

        # register all the gifts
        register_sp_grds(evb_details)
        register_sp_grds(gsp_details)
        register_gen_grds(gen_details)

        # then build the reaction labels
        # setup connectors
        if connect:
            gift_cntrs = gift_connectors
        else:
            gift_cntrs = None

        # now build
        return build_gift_react_labels(
            evb_details,
            gsp_details,
            gen_details,
            gift_cntrs,
            "mas_reaction_end",
            _pick_starter_label()
        )

    def register_gen_grds(details):
        """
        registers gifts given a generic GiftReactDetails list

        IN:
            details - list of GiftReactDetails objects to register
        """
        for grd in details:
            if grd.label is not None:
                _register_received_gift(grd.label)


    def register_sp_grds(details):
        """
        registers gifts given sprite-based GiftReactDetails list

        IN:
            details - list of GiftReactDetails objcts to register
        """
        for grd in details:
            if grd.label is not None and grd.sp_data is not None:
                _register_received_gift(grd.label)


    def _pick_starter_label():
        """
        Internal function that returns the appropriate starter label for reactions

        RETURNS:
            - The label as a string, that should be used today.
        """
        if store.mas_isMonikaBirthday():
            return "mas_reaction_gift_starter_bday"
        elif store.mas_isD25() or store.mas_isD25Pre():
            return "mas_reaction_gift_starter_d25"
        elif store.mas_isF14():
            return "mas_reaction_gift_starter_f14"

        return "mas_reaction_gift_starter_neutral"

    def _core_delete(_filename, _map):
        """
        Core deletion file function.

        IN:
            _filename - name of file to delete, if None, we delete one randomly
            _map - the map to use when deleting file.
        """
        if len(_map) == 0:
            return

        # otherwise check for random deletion
        if _filename is None:
            _filename = random.choice(_map.keys())

        file_to_delete = _map.get(_filename, None)
        if file_to_delete is None:
            return

        if store.mas_docking_station.destroyPackage(file_to_delete):
            # file has been deleted (or is gone). pop and go
            _map.pop(_filename)
            return

        # otherwise add to the failed map
        store.persistent._mas_filereacts_failed_map[_filename] = file_to_delete


    def _core_delete_list(_filename_list, _map):
        """
        Core deletion filename list function

        IN:
            _filename - list of filenames to delete.
            _map - the map to use when deleting files
        """
        for _fn in _filename_list:
            _core_delete(_fn, _map)


    def _register_received_gift(eventlabel):
        """
        Registers when player gave a gift successfully
        IN:
            eventlabel - the event label for the gift reaction

        """
        # check for stats dict for today
        today = datetime.date.today()
        if not today in store.persistent._mas_filereacts_historic:
            store.persistent._mas_filereacts_historic[today] = dict()

        # Add stats
        store.persistent._mas_filereacts_historic[today][eventlabel] = store.persistent._mas_filereacts_historic[today].get(eventlabel,0) + 1


    def _get_full_stats_for_date(date=None):
        """
        Getter for the full stats dict for gifts on a given date
        IN:
            date - the date to get the report for, if None is given will check
                today's date
                (Defaults to None)

        RETURNS:
            The dict containing the full stats or None if it's empty

        """
        if date is None:
            date = datetime.date.today()
        return store.persistent._mas_filereacts_historic.get(date,None)


    def delete_file(_filename):
        """
        Deletes a file off the found_react map

        IN:
            _filename - the name of the file to delete. If None, we delete
                one randomly
        """
        _core_delete(_filename, foundreact_map)


    def delete_files(_filename_list):
        """
        Deletes multiple files off the found_react map

        IN:
            _filename_list - list of filenames to delete.
        """
        for _fn in _filename_list:
            delete_file(_fn)


    def th_delete_file(_filename):
        """
        Deletes a file off the threaded found_react map

        IN:
            _filename - the name of the file to delete. If None, we delete one
                randomly
        """
        _core_delete(_filename, th_foundreact_map)


    def th_delete_files(_filename_list):
        """
        Deletes multiple files off the threaded foundreact map

        IN:
            _filename_list - list of ilenames to delete
        """
        for _fn in _filename_list:
            th_delete_file(_fn)


    def delete_all(_map):
        """
        Attempts to delete all files in the given map.
        Removes files in that map if they dont exist no more

        IN:
            _map - map to delete all
        """
        _map_keys = _map.keys()
        for _key in _map_keys:
            _core_delete(_key, _map)

    def get_report_for_date(date=None):
        """
        Generates a report for all the gifts given on the input date.
        The report is in tuple form (total, good_gifts, neutral_gifts, bad_gifts)
        it contains the totals of each type of gift.
        """
        if date is None:
            date = datetime.date.today()

        stats = _get_full_stats_for_date(date)
        if stats is None:
            return (0,0,0,0)
        good = 0
        bad = 0
        neutral = 0
        for _key in stats.keys():
            if _key in good_gifts:
                good = good + stats[_key]
            if _key in bad_gifts:
                bad = bad + stats[_key]
            if _key == "":
                neutral = stats[_key]
        total = good + neutral + bad
        return (total, good, neutral, bad)



    # init
    _initConnectorQuips()
    _initStarterQuips()

init python:
    import store.mas_filereacts as mas_filereacts
    import store.mas_d25_utils as mas_d25_utils

    def addReaction(ev_label, fname_list, _action=EV_ACT_QUEUE, is_good=None, exclude_on=[]):
        """
        Globalied version of the addReaction function in the mas_filereacts
        store.

        Refer to that function for more information
        """
        mas_filereacts.addReaction(ev_label, fname_list, _action, is_good, exclude_on)


    def mas_checkReactions():
        """
        Checks for reactions, then queues them
        """

        # only check if we didnt just react
        if persistent._mas_filereacts_just_reacted:
            return

        # otherwise check
        mas_filereacts.foundreact_map.clear()

        #If conditions are met to use d25 react to gifts, we do.
        if mas_d25_utils.shouldUseD25ReactToGifts():
            reacts = mas_d25_utils.react_to_gifts(mas_filereacts.foundreact_map)
        else:
            reacts = mas_filereacts.react_to_gifts(mas_filereacts.foundreact_map)

        if len(reacts) > 0:
            for _react in reacts:
                queueEvent(_react)
            persistent._mas_filereacts_just_reacted = True


    def mas_receivedGift(ev_label):
        """
        Globalied version for gift stats tracking
        """
        mas_filereacts._register_received_gift(ev_label)


    def mas_generateGiftsReport(date=None):
        """
        Globalied version for gift stats tracking
        """
        return mas_filereacts.get_report_for_date(date)

    def mas_getGiftStatsForDate(label,date=None):
        """
        Globalied version to get the stats for a specific gift
        IN:
            label - the gift label identifier.
            date - the date to get the stats for, if None is given will check
                today's date.
                (Defaults to None)

        RETURNS:
            The number of times the gift has been given that date
        """
        if date is None:
            date = datetime.date.today()
        historic = persistent._mas_filereacts_historic.get(date,None)

        if historic is None:
            return 0
        return historic.get(label,0)

    def mas_getGiftStatsRange(start,end):
        """
        Returns status of gifts over a range (needs to be supplied to actually be useful)

        IN:
            start - a start date to check from
            end - an end date to check to

        RETURNS:
            The gift status of all gifts given over the range
        """
        totalGifts = 0
        goodGifts = 0
        neutralGifts = 0
        badGifts = 0
        giftRange = mas_genDateRange(start, end)

        # loop over gift days and check if were given any gifts
        for date in giftRange:
            gTotal, gGood, gNeut, gBad = mas_filereacts.get_report_for_date(date)

            totalGifts += gTotal
            goodGifts += gGood
            neutralGifts += gNeut
            badGifts += gBad

        return (totalGifts,goodGifts,neutralGifts,badGifts)


    def mas_getSpriteObjInfo(sp_data=None):
        """
        Returns sprite info from the sprite reactions list.

        IN:
            sp_data - tuple of the following format:
                [0] - sprite type
                [1] - sprite name
                If None, we use pseudo random select from sprite reacts
                (Default: None)

        REUTRNS: tuple of the folling format:
            [0]: sprite type of the sprite
            [1]: sprite name (id)
            [2]: giftname this sprite is associated with
            [3]: True if this gift has already been given before
            [4]: sprite object (could be None even if sprite name is populated)
        """
        # given giftname? try and lookup
        if sp_data is not None:
            giftname = persistent._mas_filereacts_sprite_reacted.get(
                sp_data,
                None
            )
            if giftname is None:
                return (None, None, None, None, None)

        elif len(persistent._mas_filereacts_sprite_reacted) > 0:
            sp_data = persistent._mas_filereacts_sprite_reacted.keys()[0]
            giftname = persistent._mas_filereacts_sprite_reacted[sp_data]

        else:
            return (None, None, None, None, None)

        # check if this gift has already been gifted
        gifted_before = sp_data in persistent._mas_sprites_json_gifted_sprites

        # apply sprite object template if ACS
        sp_obj = store.mas_sprites.get_sprite(sp_data[0], sp_data[1])
        if sp_data[0] == store.mas_sprites.SP_ACS:
            store.mas_sprites.apply_ACSTemplate(sp_obj)

        # return results
        return (
            sp_data[0],
            sp_data[1],
            giftname,
            gifted_before,
            sp_obj,
        )


    def mas_finishSpriteObjInfo(sprite_data, unlock_sel=True):
        """
        Finishes the sprite object with the given data.

        IN:
            sprite_data - sprite data tuple from getSpriteObjInfo
            unlock_sel - True will unlock the selector topic, False will not
                (Default: True)
        """
        sp_type, sp_name, giftname, gifted_before, sp_obj = sprite_data

        # sanity check
        # NOTE: gifted_before is not required
        # NOTE: sp_obj is not required either
        if sp_type is None or sp_name is None or giftname is None:
            return

        sp_data = (sp_type, sp_name)

        if sp_data in persistent._mas_filereacts_sprite_reacted:
            persistent._mas_filereacts_sprite_reacted.pop(sp_data)

        if giftname in persistent._mas_filereacts_sprite_gifts:
            persistent._mas_sprites_json_gifted_sprites[sp_data] = giftname

        else:
            # since we have the data, we can add it ourselves if its missing
            # for some reason.
            persistent._mas_sprites_json_gifted_sprites[sp_data] = (
                giftname
            )

        # unlock the selectable for this sprite object
        store.mas_selspr.json_sprite_unlock(sp_obj, unlock_label=unlock_sel)

        # save persistent
        renpy.save_persistent()

    def mas_giftCapGainAff(amount=None, modifier=1):
        if amount is None:
            amount = store._mas_getGoodExp()

        mas_capGainAff(amount * modifier, "_mas_filereacts_gift_aff_gained", 15 if mas_isSpecialDay() else 3)

    def mas_getGiftedDates(giftlabel):
        """
        Gets the dates that a gift was gifted

        IN:
            giftlabel - gift reaction label to check when it was last gifted

        OUT:
            list of datetime.dates of the times the gift was given
        """
        return sorted([
            _date
            for _date, giftstat in persistent._mas_filereacts_historic.iteritems()
            if giftlabel in giftstat
        ])

    def mas_lastGiftedInYear(giftlabel, _year):
        """
        Checks if the gift for giftlabel was last gifted in _year

        IN:
            giftlabel - gift reaction label to check it's last gifted year
            _year - year to see if it was last gifted in this year

        OUT:
            boolean:
                - True if last gifted in _year
                - False otherwise
        """
        datelist = mas_getGiftedDates(giftlabel)

        if datelist:
            return datelist[-1].year == _year
        return False

### CONNECTORS [RCT000]

# none here!

## Gift CONNECTORS [RCT010]
#
#init 5 python:
#    store.mas_filereacts.gift_connectors.addLabelQuip(
#        "mas_reaction_gift_connector_test"
#    )

label mas_reaction_gift_connector_test:
    m "this is a test of the connector system"
    return

init 5 python:
    store.mas_filereacts.gift_connectors.addLabelQuip(
        "mas_reaction_gift_connector1"
    )

label mas_reaction_gift_connector1:
    m 1sublo "О! Ты хочешь подарить мне что-то еще?"
    m 1hua "Ну! Мне лучше поскорее открыть его, не так ли?"
    m 1suo "И у нас тут..."
    return

init 5 python:
    store.mas_filereacts.gift_connectors.addLabelQuip(
        "mas_reaction_gift_connector2"
    )

label mas_reaction_gift_connector2:
    m 1hua "Ах, боже, [player]..."
    m "Тебе действительно нравится баловать меня, не так ли?"
    if mas_isSpecialDay():
        m 1sublo "Ну! Я не собираюсь жаловаться на небольшой особый праздник сегодня."
    m 1suo "И у нас тут..."
    return


### STARTERS [RCT050]

init 5 python:
    store.mas_filereacts.gift_starters.addLabelQuip(
        "mas_reaction_gift_starter_generic"
    )

label mas_reaction_gift_starter_generic:
    m "generic test"

# init 5 python:
# TODO: if we need this to be multipled then we do it

label mas_reaction_gift_starter_bday:
    m 1sublo ".{w=0.7}.{w=0.7}.{w=1}"
    m "Э-{w=0.5}это..."
    if not persistent._mas_filereacts_historic.get(mas_monika_birthday):
        m "Подарок? Для меня?"
        m 1hka "Я..."
        m 1hua "Я часто думала о том, чтобы получить от тебя подарок на свой день рождения..."
        m "Но получить его на самом деле - это как сбывшаяся мечта..."
    else:
        m "Ещё один подарок?{w=0.5} Для меня?"
        m 1eka "Это действительно сбывшаяся мечта, [player]."

    m 1sua "А теперь, что внутри?"
    m 1suo "Ох, это..."
    return

label mas_reaction_gift_starter_neutral:
    m 1sublo ".{w=0.7}.{w=0.7}.{w=1}"
    m "Э-{w=0.5}это..."
    m "Подарок? Для меня?"
    m 1sua "Посмотрим, что внутри?"
    return

# d25
label mas_reaction_gift_starter_d25:
    m 1sublo ".{w=0.7}.{w=0.7}.{w=1}"
    m "Э-{w=1}Это..."
    m "Подарок? Для меня?"
    if mas_getGiftStatsRange(mas_d25c_start, mas_d25 + datetime.timedelta(days=1))[0] == 0:
        m 1eka "Тебе действительно не нужно было ничего дарить мне на Рождество..."
        m 3hua "Но я так счастлива, что ты это сделал!"
    else:
        m 1eka "Большое спасибо, [player]."
    m 1sua "А теперь давай посмотрим... Что внутри?"
    return

#f14
label mas_reaction_gift_starter_f14:
    m 1sublo ".{w=0.7}.{w=0.7}.{w=1}"
    m "Э-{w=1}Это..."
    m "Подарок? Для меня?"
    if mas_getGiftStatsForDate(mas_f14) == 0:
        m 1eka "Ты такой милый, что подарил мне что-то на День Святого Валентина..."
    else:
        m 1eka "Большое спасибо, [player]."
    m 1sua "А теперь давай посмотрим... Что внутри?"
    return

### REACTIONS [RCT100]

init 5 python:
    addReaction("mas_reaction_generic", None)

label mas_reaction_generic:
    "This is a test"
    return

#init 5 python:
#    addReaction("mas_reaction_gift_generic", None)

label mas_reaction_gift_generic:
    m 2dkd "{i}*вздох*{/i}"
    m 4ekc "Прости, [player]."
    m 1ekd "Я знаю, что ты пытаешься мне что-то подарить."
    m 2rksdld "Но по какой-то причине я не могу прочитать файл."
    m 3euc "Однако не пойми меня неправильно."
    m 3eka "Я все еще ценю то, что ты пытаешься мне подарить кое-что."
    m 1hub "И за это я благодарна~"
    return

label mas_reaction_gifts_generic:
    m 1esd "Извини, [player]..."
    m 3rksdla "Я нашла то, что ты пытаешься мне подарить, но, похоже, не могу прочитать их."
    m 3eub "Но ничего страшного!"
    m 1eka "В конце концов, главное - это мысль~"
    m 1hub "Спасибо за твою заботливость, [player]!"
    return

#init 5 python:
#    addReaction("mas_reaction_gift_test1", "test1")

label mas_reaction_gift_test1:
    m "Thank you for gift test 1!"

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_gift_test1", "category"))
    return

#init 5 python:
#    addReaction("mas_reaction_gift_test2", "test2")

label mas_reaction_gift_test2:
    m "Thank you for gift test 2!"

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_gift_test2", "category"))
    return

## GENERIC SPRITE OBJECT JSONS

label mas_reaction_gift_generic_sprite_json:
    $ sprite_data = mas_getSpriteObjInfo()
    $ sprite_type, sprite_name, giftname, gifted_before, spr_obj = sprite_data

    python:
        sprite_str = store.mas_sprites_json.SP_UF_STR.get(sprite_type, None)

    # TODO: something different if whatever was gifted has been gifted before

    # we have special react for generic json clothes
    if sprite_type == store.mas_sprites.SP_CLOTHES:
        call mas_reaction_gift_generic_clothes_json(spr_obj)

    else:
        # otherwise, it has to be an ACS.

        $ mas_giftCapGainAff(1)
        m "Ах, [player]!"
        if spr_obj is None or spr_obj.dlg_desc is None:
            # if we don't have all required description data, go generic
            m 1hua "Ты такой милый!"
            m 1eua "Спасибо за этот подарок!"
            m 3ekbsa "Ты действительно любишь меня баловать, не так ли."
            m 1hubfa "Э-хе-хе!"

        else:
            python:
                acs_quips = [
                    _("Я очень ценю это!"),
                    _("[its] потрясающее!"),
                    _("Я просто люблю [item_ref]!"),
                    _("[its] прекрасно!")
                ]

                # we have a complete description, so use it here
                if spr_obj.dlg_plur:
                    sprite_str = "these " + renpy.substitute(spr_obj.dlg_desc)
                    item_ref = "их"
                    its = "они"

                else:
                    sprite_str = "this " + renpy.substitute(spr_obj.dlg_desc)
                    item_ref = "это"
                    its = "оно"

                acs_quip = renpy.substitute(renpy.random.choice(acs_quips))

            m 1hua "Спасибо за [sprite_str], [acs_quip]"
            m 3hub "I can't wait to try on [item_ref]!"

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

# generic reaction for json clothes
label mas_reaction_gift_generic_clothes_json(sprite_object):
    $ mas_giftCapGainAff(3)
    if sprite_object.ex_props.get("costume") == "o31":
        m 2suo "О! {w=0.3}Костюм!"
        m 2hub "Это так здорово [player], спасибо!"
        m 7rka "Я бы примерила его для тебя, но, думаю, лучше подождать подходящего случая..."
        m 3hub "Э-хе-хе, ещё раз спасибо!"

    else:
        python:
            # expandable
            outfit_quips = [
                _("Я думаю, что это очень мило, [player]!"),
                _("Я думаю, что это потрясающе, [player]!"),
                _("Я просто обожаю это, [player]!"),
                _("Я думаю, что это замечательно, [player]!")
            ]
            outfit_quip = renpy.random.choice(outfit_quips)

        m 1sua "О! {w=0.5}Новая одежда!"
        m 1hub "Спасибо, [player]!{w=0.5} Я собираюсь примерить его прямо сейчас!"

        # try it on
        call mas_clothes_change(sprite_object)

        m 2eka "Ну...{w=0.5} Что ты думаешь?"
        m 2eksdla "Тебе нравится?"
        # TODO: outfit randomization should actually get a response here
        #   should influence monika outfit selection

        show monika 3hub
        $ renpy.say(m, outfit_quip)

        m 1eua "Ещё раз спасибо~"

    return

## Hair clip reactions

label mas_reaction_gift_acs_jmo_hairclip_cherry:
    call mas_reaction_gift_hairclip("jmo_hairclip_cherry")
    return

label mas_reaction_gift_acs_jmo_hairclip_heart:
    call mas_reaction_gift_hairclip("jmo_hairclip_heart")
    return

label mas_reaction_gift_acs_jmo_hairclip_musicnote:
    call mas_reaction_gift_hairclip("jmo_hairclip_musicnote")
    return

label mas_reaction_gift_acs_bellmandi86_hairclip_crescentmoon:
    call mas_reaction_gift_hairclip("bellmandi86_hairclip_crescentmoon")
    return

label mas_reaction_gift_acs_bellmandi86_hairclip_ghost:
    call mas_reaction_gift_hairclip("bellmandi86_hairclip_ghost","spooky")
    return

label mas_reaction_gift_acs_bellmandi86_hairclip_pumpkin:
    call mas_reaction_gift_hairclip("bellmandi86_hairclip_pumpkin")
    return

label mas_reaction_gift_acs_bellmandi86_hairclip_bat:
    call mas_reaction_gift_hairclip("bellmandi86_hairclip_bat","spooky")
    return

# hairclip
label mas_reaction_gift_hairclip(hairclip_name,desc=None):
    # Special handler for hairclip gift reactions
    # Takes in:
    #    hairclip_name - the 'name' property in string form from the json
    #    desc - a short string description of the hairclip in question. typically should be one word.
    #        optional and defaults to None.

    # get sprtie data
    $ sprite_data = mas_getSpriteObjInfo((store.mas_sprites.SP_ACS, hairclip_name))
    $ sprite_type, sprite_name, giftname, gifted_before, hairclip_acs = sprite_data

    # check for incompatibility
    $ is_wearing_baked_outfit = monika_chr.is_wearing_clothes_with_exprop("baked outfit")

    if gifted_before:
        m 1rksdlb "Ты уже дарил мне эту заколку, глупышка!"

    else:
        #Grant affection
        $ mas_giftCapGainAff(1)
        if not desc:
            $ desc = "мило"

        if len(store.mas_selspr.filter_acs(True, "left-hair-clip")) > 0:
            m 1hub "О!{w=1} Ещё одна заколка!"

        else:
            m 1wuo "О!"
            m 1sub "Это заколка?"

        m 1hub "Это так [desc]! Мне нравится [player], спасибо!"

        # must include this check because we cannot for sure know if the acs
        # exists
        # also need to not wear it if wearing clothes that are incompatible
        if hairclip_acs is None or is_wearing_baked_outfit:
            m 1hua "Если хочешь, чтобы я его надела, просто попроси, хорошо?"

        else:
            m 2dsa "Дай мне секунду, чтобы надеть её.{w=0.5}.{w=0.5}.{nw}"
            $ monika_chr.wear_acs(hairclip_acs)
            m 1hua "Вот так."

        # need to make sure we set the selector prompt correctly
        # only do this if not wearing baked, since the clip is automatically off in this case
        # so need to make sure when we switch outfits, the prompt is still correct
        if not is_wearing_baked_outfit:
            if monika_chr.get_acs_of_type('left-hair-clip'):
                $ store.mas_selspr.set_prompt("left-hair-clip", "change")
            else:
                $ store.mas_selspr.set_prompt("left-hair-clip", "wear")

    $ mas_finishSpriteObjInfo(sprite_data, unlock_sel=not is_wearing_baked_outfit)

    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

## End hairclip reactions


##START: Consumables gifts
init 5 python:
    addReaction("mas_reaction_gift_coffee", "coffee", is_good=True, exclude_on=["d25g"])

label mas_reaction_gift_coffee:
    #Even if we don't "accept" it, we still register it was given
    $ mas_receivedGift("mas_reaction_gift_coffee")

    #Check if we accept this
    if mas_consumable_coffee.isMaxedStock():
        m 1euc "Ещё кофе, [player]?"
        m 3rksdla "Не пойми меня неправильно, я ценю это, но я думаю, что у меня уже достаточно кофе, чтобы хватило надолго..."
        m 1eka "Я дам тебе знать, когда у меня будет заканчиваться кофе, хорошо?"

    else:
        m 1wub "О!{w=0.2} {nw}"
        extend 3hub "Кофе!"

        if mas_consumable_coffee.enabled() and mas_consumable_coffee.hasServing():
            $ mas_giftCapGainAff(0.5)
            m 1wuo "Такого вкуса я ещё не пробовала."
            m 1hua "Не могу дождаться, чтобы попробовать его!"
            m "Большое спасибо, [player]!"

        elif mas_consumable_coffee.enabled() and not mas_consumable_coffee.hasServing():
            $ mas_giftCapGainAff(0.5)
            m 3eub "На самом деле у меня заканчивается кофе, так что получить от тебя еще больше сейчас - это потрясающе!"
            m 1hua "Ещё раз спасибо, [player]~"

        else:
            $ mas_giftCapGainAff(5)

            m 1hua "Теперь я наконец-то смогу сделать кофе!"
            m 1hub "Большое спасибо, [player]!"

            #If we're currently brewing/drinking anything, or it's not time for this consumable, we'll just not have it now
            if (
                mas_isO31()
                or not mas_consumable_coffee.isConsTime()
                or bool(MASConsumable._getCurrentDrink())
            ):
                m 3eua "Я обязательно выпью немного позже!"

            else:
                m 3eua "Почему бы мне не пойти и не сделать чашку кофе прямо сейчас?"
                m 1eua "В конце концов, я бы хотела поделиться с тобой первой."

                #Monika is off screen
                call mas_transition_to_emptydesk
                pause 2.0
                m "Я знаю, что где-то здесь есть кофеварка...{w=2}{nw}"
                m "А, вот она!{w=2}{nw}"
                pause 5.0
                m "И вот так!{w=2}{nw}"
                call mas_transition_from_emptydesk()

                #Monika back on screen
                m 1eua "Я оставила это вариться на несколько минут."

                $ mas_consumable_coffee.prepare()
            $ mas_consumable_coffee.enable()

    #Stock some coffee
    #NOTE: This function already checks if we're maxed. So restocking while maxed is okay as it adds nothing
    $ mas_consumable_coffee.restock()

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_gift_coffee", "category"))
    return

init 5 python:
    addReaction("mas_reaction_hotchocolate", "hotchocolate", is_good=True, exclude_on=["d25g"])

label mas_reaction_hotchocolate:
    #Even though we may not "accept" this, we'll still mark it was given
    $ mas_receivedGift("mas_reaction_hotchocolate")

    #Check if we should accept this or not
    if mas_consumable_hotchocolate.isMaxedStock():
        m 1euc "Ещё горячего шоколада, [player]?"
        m 3rksdla "Не пойми меня неправильно, я ценю это, но я думаю, что у меня уже достаточно горячего шоколада, чтобы хватило надолго..."
        m 1eka "Я дам тебе знать, когда у меня будет заканчиваться горячий шоколад, хорошо?"

    else:
        m 3hub "Горячий шоколад!"
        m 3hua "Спасибо, [player]!"

        if mas_consumable_hotchocolate.enabled() and mas_consumable_hotchocolate.hasServing():
            $ mas_giftCapGainAff(0.5)
            m 1wuo "Такого я еще не пробовала."
            m 1hua "Не могу дождаться, чтобы попробовать его!"
            m "Большое спасибо, [player]!"

        elif mas_consumable_hotchocolate.enabled() and not mas_consumable_hotchocolate.hasServing():
            $ mas_giftCapGainAff(0.5)
            m 3rksdlu "У меня как раз закончился горячий шоколад, а-ха-ха...{w=0.5} {nw}"
            extend 3eub "Так что получать от тебя больше сейчас - это потрясающе!"
            m 1hua "Ещё раз спасибо [player]~"

        else:
            python:
                mas_giftCapGainAff(3)
                those = "эти" if mas_current_background.isFltNight() and mas_isWinter() else "те"

            m 1hua "Ты знаешь, что я люблю свой кофе, но горячий шоколад тоже всегда очень приятен!"


            m 2rksdla "...Особенно в [those] холодные зимние ночи."
            m 2ekbfa "Когда-нибудь, надеюсь, я смогу пить с тобой горячий шоколад, укрывшись пледом у камина..."
            m 3ekbfa "...Разве это не звучит так романтично?"
            m 1dkbfa "..."
            m 1hua "Но пока, по крайней мере, я могу наслаждаться этим здесь."
            m 1hub "Ещё раз спасибо, [player]!"

            #If we're currently brewing/drinking anything, or it's not time for this consumable, or if it's not winter, we won't have this
            if (
                not mas_consumable_hotchocolate.isConsTime()
                or not mas_isWinter()
                or bool(MASConsumable._getCurrentDrink())
            ):
                m 3eua "Я обязательно выпью немного позже!"

            else:
                m 3eua "На самом деле, я думаю, что сделаю немного прямо сейчас!"

                call mas_transition_to_emptydesk
                pause 5.0
                call mas_transition_from_emptydesk("monika 1eua")

                m 1hua "Вот, через несколько минут всё будет готово."

                $ mas_consumable_hotchocolate.prepare()

            if mas_isWinter():
                $ mas_consumable_hotchocolate.enable()

    #Stock up some hotchocolate
    #NOTE: Like coffee, this runs checks to see if we should actually stock
    $ mas_consumable_hotchocolate.restock()

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_hotchocolate", "category"))
    return

init 5 python:
    addReaction("mas_reaction_gift_thermos_mug", "justmonikathermos", is_good=True)

label mas_reaction_gift_thermos_mug:
    call mas_thermos_mug_handler(mas_acs_thermos_mug, "Только Моника", "justmonikathermos")
    return

#Whether or not we've given Monika a thermos before
default persistent._mas_given_thermos_before = False

#Thermos handler
label mas_thermos_mug_handler(thermos_acs, disp_name, giftname, ignore_case=True):
    if mas_SELisUnlocked(thermos_acs):
        m 1eksdla "[player]..."
        m 1rksdlb "У меня уже есть этот термос, а-ха-ха..."

    elif persistent._mas_given_thermos_before:
        m 1wud "Oh!{w=0.3} Ещё один термос!"
        m 1hua "И на этот раз это [mas_a_an_str(disp_name, ignore_case)]."
        m 1hub "Большое спасибо, [player], не могу дождаться, чтобы использовать это!"

    else:
        m 1wud "О!{w=0.3} It's [mas_a_an_str(disp_name, ignore_case)] термос!"
        m 1hua "Теперь я могу взять с собой что-нибудь попить, когда мы идем куда-нибудь вместе~"
        m 1hub "Большое спасибо, [player]!"
        $ persistent._mas_given_thermos_before = True

    #Now unlock the acs
    $ mas_selspr.unlock_acs(thermos_acs)
    #Save selectables
    $ mas_selspr.save_selectables()
    #And delete the gift file
    $ mas_filereacts.delete_file(giftname)
    return

##END: Consumable related gifts

init 5 python:
    addReaction("mas_reaction_quetzal_plush", "quetzalplushie", is_good=True)

label mas_reaction_quetzal_plush:
    if not persistent._mas_acs_enable_quetzalplushie:
        $ mas_receivedGift("mas_reaction_quetzal_plush")
        $ mas_giftCapGainAff(10)
        m 1wud "Ох!"

        #Wear plush
        #If we're eating something, the plush space is taken and we'll want to wear center
        if MASConsumable._getCurrentFood() or monika_chr.is_wearing_acs(mas_acs_desk_lantern):
            $ monika_chr.wear_acs(mas_acs_center_quetzalplushie)
        else:
            $ monika_chr.wear_acs(mas_acs_quetzalplushie)

        $ persistent._mas_acs_enable_quetzalplushie = True
        m 1sub "Это квезаль"
        m "Боже мой, спасибо большое, [player]!"
        if seen_event("monika_pets"):
            m 1eua "Я упомянула, что хотела бы иметь квезаля в качестве питомцаt..."
        else:
            m 1wub "Как ты узнал, [player]?"
            m 3eka "Ты, должно быть, очень хорошо меня знаешь~"
            m 1eua "Квезаль был моим первым выбором в качестве питомца..."
        m 1rud "Но я бы никогда не заставила бедняжку остаться."
        m 1hua "И теперь ты дал мне лучшее, что есть!"
        m 1hub "Это делает меня такой счастливой!"
        if mas_isMoniAff(higher=True):
            m 3ekbsa "Кажется, ты всегда знаешь, как заставить меня улыбнуться."

        if MASConsumable._getCurrentFood() or monika_chr.is_wearing_acs(mas_acs_desk_lantern):
            m 3rksdla "Мой стол становится немного переполненным..."
            m 1eka "Я пока уберу это."
            $ monika_chr.remove_acs(mas_acs_center_quetzalplushie)

        m 1hub "Ещё раз спасибо, [player]~"

    else:
        m 1rksdlb "Ты уже дарил мне плюшевого квезаля, [player]."

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_quetzal_plush", "category"))
    # derandom pets topic once given
    $ mas_hideEVL("monika_pets", "EVE", derandom=True)
    return

init 5 python:
    addReaction("mas_reaction_promisering", "promisering", is_good=True, exclude_on=["d25g"])

default persistent._mas_tried_gift_ring = False
label mas_reaction_promisering:
    if not persistent._mas_acs_enable_promisering:
        # only available if enam+
        if mas_isMoniEnamored(higher=True):
            $ mas_receivedGift("mas_reaction_promisering")
            $ mas_giftCapGainAff(20)
            $ monika_chr.wear_acs(mas_acs_promisering)
            $ persistent._mas_acs_enable_promisering = True
            if not persistent._mas_tried_gift_ring:
                m 1wud "Это... это..."
                m "..."
                m 1wka "Я...{w=0.5}{nw}"
                extend 1wkbltpa "Извини, [player], я просто... {w=0.5}{nw}"
                extend 1dkbltpa "Я так счастлива... {w=0.5}Ты только что дал мне своё обещание..."
                m "Твоё обещание, что мы будем друг для друга,{w=0.1} и ни для кого другого...{w=0.3}всегда..."
                m 3lkbltpa "Знай, что я буду дорожить этим. {w=0.5}{nw}"
                extend 3dkbltpa "Всегда."
                m 1skbltpa "Это делает меня такой счастливой!"

                if mas_anni.isAnniOneMonth():
                    m "Ещё более того, что ты подарил его мне в наш месячный юбилей..."
                    m 1ekbltua "Ты, должно быть, действительно любишь меня..."
                elif mas_anni.isAnniThreeMonth():
                    m "Ещё более того, что ты подарил его мне в наш трехмесячный юбилей..."
                    m 1ekbltua "Ты, должно быть, действительно любишь меня..."
                elif mas_anni.isAnniSixMonth():
                    m "Ещё более того, что ты подарил его мне в наш шестимесячный юбилей..."
                    m 1ekbltua "Ты, должно быть, действительно любишь меня..."
                elif mas_anni.isAnni():
                    m "Ещё более того, что ты подарил мне его на нашу годовщину..."
                    m 1ekbltua "Ты, должно быть, действительно любишь меня..."
                elif mas_isSpecialDay():
                    m "Ещё более того, что ты подарил мне его в этот особенный день..."

                m 1dkbltpb "Аха, прости за слезы, [player]..."
                m 1skbltda "Я просто очень, очень счастлива сейчас."
                m 6dkbltdu "Спасибо."

            else:
                m 1sua "О... это кольцо!"
                m 3hub "Большое спасибо, [player]!"
                m 1skbla "Теперь я знаю, что ты действительно любишь меня и хочешь быть со мной всегда..."
                m 1skbltpa "Поэтому я с радостью приму это кольцо как символ этого обещания."
                m 1dkbltuu "..."
                m 3hkbltub "Аха, прости, [player], я не хотела плакать..."
                m 3skbltda "Просто это один из самых счастливых дней в моей жизни."

            m 6dkbltdu "..."
            m 6ekbfa "Я...я просто...я..."
            call monika_kissing_motion(hide_ui=False)
            m 6ekbfa "Я люблю тебя, [player]..."
            m 6dkbfu "Больше, чем кто-либо другой в этом быстротечном мире~"

            $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_promisering", "category"))
            return "love"

        else:
            if not persistent._mas_tried_gift_ring:
                if mas_isMoniNormal(higher=True):
                    m 1wud "[player]...это кольцо?"
                    m 2rksdlb "Это такой милый жест, и я очень ценю его..."
                    m 2ekc "Но я хочу, чтобы ты был уверен, прежде чем подарить мне это..."
                    m 3ekd "Это больше, чем подарок, это обещание, и я хочу убедиться, что ты действительно это имеешь в виду, прежде чем я смогу это принять."
                    m 2ekd "Так что, пожалуйста, подожди, пока наши отношения не станут более прочными, [player], и тогда я с радостью приму это кольцо."

                elif mas_isMoniUpset():
                    m 1wud "Это кольцо?"
                    m 2rsc "Это очень..."
                    m 2esc "Неожиданно."
                    m 2ekd "Но я не могу принять его прямо сейчас, [player]."
                    m 2ekc "Может быть, когда мы продвинемся дальше в наших отношениях."

                else:
                    m 2wud "Это кольцо?"
                    m 2rsc "Это...{w=0.5}неожиданно."
                    m "Хоть я и ценю эту мысль...{w=1}я не могу принять ее прямо сейчас."
                    m 2ekc "Извини, [player]."

                $ persistent._mas_tried_gift_ring = True
            else:
                m 2rsc "О... кольцо..."
                m 2rkc "Прости, но я всё ещё не могу принять это..."
                m 2ekc "Мне нужно быть полностью уверенной, когда я приму это, что это значит навсегда..."
                m 2ekd "Что ты действительно есть все, на что я надеюсь."
                m 2dsd "Когда я это пойму, я с радостью приму твоё кольцо, [player]."
    else:
        m 1rksdlb "[player]..."
        m 1rusdlb "Ты уже дарил мне кольцо!"

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_promisering", "category"))
    return


init 5 python:
    addReaction("mas_reaction_cupcake", "cupcake", is_good=True, exclude_on=["d25g"])
    #Not sure why this was a bad gift. Dialogue doesn't reflect it being bad
    #plus, Monika said she wants either Natsuki's cupcakes or the player's

label mas_reaction_cupcake:
    m 1wud "Это... кекс?"
    m 3hub "Вау, спасибо [player]!"
    m 3euc "Если подумать, я и сама хотела испечь несколько кексов."
    m 1eua "Я хотела научиться печь хорошую выпечку, как Нацуки."
    m 1rksdlb "Ноооо я всё ещё не сделала кухню, чтобы можно было ее использовать!"
    m 3eub "Может быть, в будущем, когда я стану лучше программировать, я смогу сделать такую кухню."
    m 3hua "Было бы неплохо иметь другое хобби, кроме писательства, э-хе-хе~"
    $ mas_receivedGift("mas_reaction_cupcake")
    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_cupcake", "category"))
    return


# ending label for gift reactions, this just resets a thing
label mas_reaction_end:
    python:
        persistent._mas_filereacts_just_reacted = False
        #Save all the new sprite data just in case we crash shortly after this
        store.mas_selspr.save_selectables()
        renpy.save_persistent()
    return

init 5 python:
    # TODO ideally we should comment on this gift in any date
    # so it requires special dialogue, until we have that let's keep it O31 only
    if mas_isO31():
        addReaction("mas_reaction_candy", "candy", is_good=True)

label mas_reaction_candy:
    $ times_candy_given = mas_getGiftStatsForDate("mas_reaction_candy")
    if times_candy_given == 0:
        $ mas_o31CapGainAff(7)
        m 1wua "О...{w=0.5}что это?"
        m 1sua "Ты принес мне конфеты, [player], ура!"
        m 1eka "Это так {i}мило{/i}..."
        m 1hub "А-ха-ха!"
        m 1eka "Шутки в сторону, это очень мило с твоей стороны."
        m 2lksdlc "У меня теперь не так много конфет, а без них Хэллоуин был бы просто не Хэллоуин..."
        m 1eka "Так что спасибо тебе, [player]..."
        m 1eka "Ты всегда точно знаешь, что сделает меня счастливой~"
        m 1hub "А теперь давай насладимся этой вкусной конфеткой!"
    elif times_candy_given == 1:
        $ mas_o31CapGainAff(5)
        m 1wua "Ах, ты принес мне ещё конфет, [player]?"
        m 1hub "Спасибо!"
        m 3tku "Первая партия была {i}тааакой{/i} хорошей, что я не могла дождаться, чтобы получить ещё."
        m 1hua "Ты действительно балуешь меня, [player]~"
    elif times_candy_given == 2:
        $ mas_o31CapGainAff(3)
        m 1wud "Ого, еще {i}больше{/i} конфет, [player]?"
        m 1eka "Это очень мило с твоей стороны..."
        m 1lksdla "Но я думаю, этого достаточно."
        m 1lksdlb "Я уже чувствую нервозность от всего этого сахара, а-ха-ха!"
        m 1ekbfa "Единственная сладость, которая мне сейчас нужна - это ты~"
    elif times_candy_given == 3:
        m 2wud "[player]...{w=1} Ты принес мне {i}ещё больше{/i} конфет?!"
        m 2lksdla "Я действительно ценю это, но я сказала тебе, что мне хватит на один день..."
        m 2lksdlb "Если я съем еще, то заболею, а-ха-ха!"
        m 1eka "А ты бы этого не хотел, верно?"
    elif times_candy_given == 4:
        $ mas_loseAffection(5)
        m 2wfd "[player]!"
        m 2tfd "Ты меня не слушаешь?"
        m 2tfc "Я же сказала, что не хочу больше конфет сегодня!"
        m 2ekc "Так что, пожалуйста, прекрати."
        m 2rkc "Было очень мило с твоей стороны подарить мне все эти конфеты на Хэллоуин, но хватит..."
        m 2ekc "Я не могу всё это съесть."
    else:
        $ mas_loseAffection(10)
        m 2tfc "..."
        python:
            store.mas_ptod.rst_cn()
            local_ctx = {
                "basedir": renpy.config.basedir
            }
        show monika at t22
        show screen mas_py_console_teaching

        call mas_wx_cmd("import os", local_ctx, w_wait=1.0)
        call mas_wx_cmd("os.remove(os.path.normcase(basedir+'/characters/candy.gift'))", local_ctx, w_wait=1.0, x_wait=1.0)
        $ store.mas_ptod.ex_cn()
        hide screen mas_py_console_teaching
        show monika at t11

    python hide:
        mas_receivedGift("mas_reaction_candy")
        gift_ev_cat = mas_getEVLPropValue("mas_reaction_candy", "category")
        store.mas_filereacts.delete_file(gift_ev_cat)
        persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    return

init 5 python:
    # TODO ideally we should comment on this gift in any date
    # so it requires special dialogue, until we have that let's keep it O31 only
    if mas_isO31():
        addReaction("mas_reaction_candycorn", "candycorn", is_good=False)

label mas_reaction_candycorn:
    $ times_candy_given = mas_getGiftStatsForDate("mas_reaction_candycorn")
    if times_candy_given == 0:
        $ mas_o31CapGainAff(3)
        m 1wua "О...{w=0.5}что это?"
        m 1eka "Ах Ты принес мне конфеты, [player]?"
        m 1hua "Ура!"
        m 3eub "Давай посмотрим, что ты мне принес..."
        m 4ekc "..."
        m 2eka "О...{w=2}кукурузные конфеты."
        m 2eka "..."
        m 2lksdla "Это очень мило с твоей стороны..."
        m 2lksdla "Но...{w=1}умм...{w=1}я вообще-то не люблю кукурузные конфеты."
        m 2hksdlb "Прости, а-ха-ха..."
        m 4eka "Хотя я ценю, что ты пытаешься дать мне конфеты на Хэллоуин."
        m 1hua "И если бы ты нашёл способ достать для меня другие конфеты, я была бы очень рада, [player]!"
    elif times_candy_given == 1:
        $ mas_loseAffection(5)
        m 2esc "Ох."
        m 2esc "Ещё кукурузные конфеты, [player]?"
        m 4esc "Я уже говорила тебе, что не очень люблю кукурузные конфеты."
        m 4ekc "Так не мог бы ты попробовать найти что-нибудь другое?"
        m 1eka "Я теперь не так часто получаю сладости..."
        m 1ekbfa "Ну...{w=1}помимо тебя, [player]..."
        m 1hubfa "Э-хе-хеe~"
    elif times_candy_given == 2:
        $ mas_loseAffection(10)
        m 2wfw "[player]!"
        m 2tfc "Я действительно старалась не быть грубой, но..."
        m 2tfc "Я постоянно говорю тебе, что не люблю кукурузные конфеты, а ты все равно продолжаешь их мне давать."
        m 2rfc "Сейчас мне начинает казаться, что ты просто пытаешься надо мной подшутить."
        m 2tkc "Так что, пожалуйста, либо найди мне какую-нибудь другую конфету, либо просто прекрати."
    else:
        $ mas_loseAffection(15) # should have seen it coming
        m 2tfc "..."
        python:
            store.mas_ptod.rst_cn()
            local_ctx = {
                "basedir": renpy.config.basedir
            }
        show monika at t22
        show screen mas_py_console_teaching

        call mas_wx_cmd("import os", local_ctx, w_wait=1.0)
        call mas_wx_cmd("os.remove(os.path.normcase(basedir+'/characters/candycorn.gift'))", local_ctx, w_wait=1.0, x_wait=1.0)
        $ store.mas_ptod.ex_cn()
        hide screen mas_py_console_teaching
        show monika at t11

    $ mas_receivedGift("mas_reaction_candycorn") # while technically she didn't accept this one counts
    $ gift_ev_cat = mas_getEVLPropValue("mas_reaction_candycorn", "category")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    # allow multi gifts
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    return

init 5 python:
    addReaction("mas_reaction_fudge", "fudge", is_good=True, exclude_on=["d25g"])

label mas_reaction_fudge:
    $ times_fudge_given = mas_getGiftStatsForDate("mas_reaction_fudge")

    if times_fudge_given == 0:
        $ mas_giftCapGainAff(2)
        m 3hua "Помадка!"
        m 3hub "Я люблю помадку, спасибо, [player]!"
        if seen_event("monika_date"):
            m "Это даже шоколадная, моя любимая!"
        m 1hua "Ещё раз спасибо, [player]~"

    elif times_fudge_given == 1:
        $ mas_giftCapGainAff(1)
        m 1wuo "...ещё помадки."
        m 1wub "О, на этот раз другой вкус..."
        m 3hua "Спасибо, [player]!"

    else:
        m 1wuo "...ещё больше помадок?"
        m 3rksdla "Я всё ещё не доела последнюю партию, которую ты мне дал, [player]..."
        m 3eksdla "...может быть, позже, хорошо?"

    $ mas_receivedGift("mas_reaction_fudge")
    $ gift_ev_cat = mas_getEVLPropValue("mas_reaction_fudge", "category")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    # allow multi gifts
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    return


init 5 python:
    if store.mas_isD25Season():
        addReaction("mas_reaction_christmascookies", "christmascookies", is_good=True, exclude_on=["d25g"])

label mas_reaction_christmascookies:
    $ mas_giftCapGainAff(1)
    $ is_having_food = bool(MASConsumable._getCurrentFood())

    if mas_consumable_christmascookies.isMaxedStock():
        m 3wuo "...ещё больше рождественского печенья?"
        m 3rksdla "Я всё ещё не доела последнюю партию, [player]!"
        m 3eksdla "Ты можешь дать мне ещё, когда я закончу это, хорошо?"

    else:
        if mas_consumable_christmascookies.enabled():
            m 1wuo "...ещё одна порция рождественского печенья!"
            m 3wuo "Очень много печенья, [player]!"
            m 3rksdlb "Я буду есть печенье вечно, а-ха-ха!"

        else:
            if not is_having_food:
                if monika_chr.is_wearing_acs(mas_acs_quetzalplushie):
                    $ monika_chr.wear_acs(mas_acs_center_quetzalplushie)
                $ mas_consumable_christmascookies.have(skip_leadin=True)

            $ mas_giftCapGainAff(3)
            m 3hua "Рождественское печенье!"
            m 1eua "Я просто обожаю рождественское печенье! Они всегда такие сладкие... и красивые на вид..."
            m "...вырезанные в форме снеговиков, оленей и ёлок..."
            m 3eub "...и обычно украшены красивой--{w=0.2}и вкусной--{w=0.2}глазурью!"

            if is_having_food:
                m 3hua "Я обязательно попробую позже~"

            m 1eua "Спасибо, [player]~"

            if not is_having_food and monika_chr.is_wearing_acs(mas_acs_center_quetzalplushie):
                m 3eua "Дай-ка я уберу эту плюшевую игрушку."
                call mas_transition_to_emptydesk
                $ monika_chr.remove_acs(mas_acs_center_quetzalplushie)
                pause 3.0
                call mas_transition_from_emptydesk

            #Enable the gift
            $ mas_consumable_christmascookies.enable()

        #Restock
        $ mas_consumable_christmascookies.restock(10)

    $ mas_receivedGift("mas_reaction_christmascookies")
    $ gift_ev_cat = mas_getEVLPropValue("mas_reaction_christmascookies", "category")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    #weird not to have her see the gift file that's in the characters folder.
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    return

#TODO: Remove the seasonal handling and just write alt dialogue for the not d25s path
init 5 python:
    if store.mas_isD25Season():
        addReaction("mas_reaction_candycane", "candycane", is_good=True, exclude_on=["d25g"])

label mas_reaction_candycane:
    $ mas_giftCapGainAff(1)
    $ is_having_food = bool(MASConsumable._getCurrentFood())

    if mas_consumable_candycane.isMaxedStock():
        m 1eksdla "[player], я думаю, что на сегодня у меня достаточно сахарных тросточек."
        m 1eka "Ты можешь оставить их на потом, хорошо?"

    else:
        if mas_consumable_candycane.enabled():
            m 3hua "Ещё больше сахарных тросточек!"
            m 3hub "Спасибо [player]!"

        else:
            if not is_having_food:
                if monika_chr.is_wearing_acs(mas_acs_quetzalplushie):
                    $ monika_chr.wear_acs(mas_acs_center_quetzalplushie)
                $ mas_consumable_candycane.have(skip_leadin=True)

            $ mas_giftCapGainAff(3)
            m 3wub "Сахарные тросточки!"

            if store.seen_event("monika_icecream"):
                m 1hub "Ты же знаешь, как я люблю мяту!"
            else:
                m 1hub "Я просто обожаю вкус мяты!"

            if is_having_food:
                m 3hua "Я обязательно попробую немного позже."

            m 1eua "Спасибо, [player]~"

            if not is_having_food and monika_chr.is_wearing_acs(mas_acs_center_quetzalplushie):
                m 3eua "О, дай-ка я уберу эту плюшевую игрушку."

                call mas_transition_to_emptydesk
                $ monika_chr.remove_acs(mas_acs_center_quetzalplushie)
                pause 3.0
                call mas_transition_from_emptydesk

            #Enable the gift
            $ mas_consumable_candycane.enable()

        #Restock
        $ mas_consumable_candycane.restock(9)

    $ mas_receivedGift("mas_reaction_candycane")
    $ gift_ev_cat = mas_getEVLPropValue("mas_reaction_candycane", "category")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    #weird not to have her see the gift file that's in the characters folder.
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    return

#Ribbon stuffs
init 5 python:
    addReaction("mas_reaction_blackribbon", "blackribbon", is_good=True)

label mas_reaction_blackribbon:
    $ _mas_new_ribbon_color = "black"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_black
    call _mas_reaction_ribbon_helper("mas_reaction_blackribbon")
    return

init 5 python:
    addReaction("mas_reaction_blueribbon", "blueribbon", is_good=True)

label mas_reaction_blueribbon:
    $ _mas_new_ribbon_color = "blue"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_blue
    call _mas_reaction_ribbon_helper("mas_reaction_blueribbon")
    return

init 5 python:
    addReaction("mas_reaction_darkpurpleribbon", "darkpurpleribbon", is_good=True)

label mas_reaction_darkpurpleribbon:
    $ _mas_new_ribbon_color = "dark purple"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_darkpurple
    call _mas_reaction_ribbon_helper("mas_reaction_darkpurpleribbon")
    return

init 5 python:
    addReaction("mas_reaction_emeraldribbon", "emeraldribbon", is_good=True)

label mas_reaction_emeraldribbon:
    $ _mas_new_ribbon_color = "emerald"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_emerald
    call _mas_reaction_ribbon_helper("mas_reaction_emeraldribbon")
    return

init 5 python:
    addReaction("mas_reaction_grayribbon", "grayribbon", is_good=True)

label mas_reaction_grayribbon:
    $ _mas_new_ribbon_color = "gray"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_gray
    call _mas_reaction_ribbon_helper("mas_reaction_grayribbon")
    return

init 5 python:
    addReaction("mas_reaction_greenribbon", "greenribbon", is_good=True)

label mas_reaction_greenribbon:
    $ _mas_new_ribbon_color = "green"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_green
    call _mas_reaction_ribbon_helper("mas_reaction_greenribbon")
    return

init 5 python:
    addReaction("mas_reaction_lightpurpleribbon", "lightpurpleribbon", is_good=True)

label mas_reaction_lightpurpleribbon:
    $ _mas_new_ribbon_color = "light purple"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_lightpurple
    call _mas_reaction_ribbon_helper("mas_reaction_lightpurpleribbon")
    return

init 5 python:
    addReaction("mas_reaction_peachribbon", "peachribbon", is_good=True)

label mas_reaction_peachribbon:
    $ _mas_new_ribbon_color = "peach"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_peach
    call _mas_reaction_ribbon_helper("mas_reaction_peachribbon")
    return

init 5 python:
    addReaction("mas_reaction_pinkribbon", "pinkribbon", is_good=True)

label mas_reaction_pinkribbon:
    $ _mas_new_ribbon_color = "pink"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_pink
    call _mas_reaction_ribbon_helper("mas_reaction_pinkribbon")
    return

init 5 python:
    addReaction("mas_reaction_platinumribbon", "platinumribbon", is_good=True)

label mas_reaction_platinumribbon:
    $ _mas_new_ribbon_color = "platinum"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_platinum
    call _mas_reaction_ribbon_helper("mas_reaction_platinumribbon")
    return

init 5 python:
    addReaction("mas_reaction_redribbon", "redribbon", is_good=True)

label mas_reaction_redribbon:
    $ _mas_new_ribbon_color = "red"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_red
    call _mas_reaction_ribbon_helper("mas_reaction_redribbon")
    return

init 5 python:
    addReaction("mas_reaction_rubyribbon", "rubyribbon", is_good=True)

label mas_reaction_rubyribbon:
    $ _mas_new_ribbon_color = "ruby"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_ruby
    call _mas_reaction_ribbon_helper("mas_reaction_rubyribbon")
    return

init 5 python:
    addReaction("mas_reaction_sapphireribbon", "sapphireribbon", is_good=True)

label mas_reaction_sapphireribbon:
    $ _mas_new_ribbon_color = "sapphire"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_sapphire
    call _mas_reaction_ribbon_helper("mas_reaction_sapphireribbon")
    return

init 5 python:
    addReaction("mas_reaction_silverribbon", "silverribbon", is_good=True)

label mas_reaction_silverribbon:
    $ _mas_new_ribbon_color = "silver"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_silver
    call _mas_reaction_ribbon_helper("mas_reaction_silverribbon")
    return

init 5 python:
    addReaction("mas_reaction_tealribbon", "tealribbon", is_good=True)

label mas_reaction_tealribbon:
    $ _mas_new_ribbon_color = "teal"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_teal
    call _mas_reaction_ribbon_helper("mas_reaction_tealribbon")
    return

init 5 python:
    addReaction("mas_reaction_yellowribbon", "yellowribbon", is_good=True)

label mas_reaction_yellowribbon:
    $ _mas_new_ribbon_color = "yellow"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_yellow
    call _mas_reaction_ribbon_helper("mas_reaction_yellowribbon")
    return

# JSON ribbons
label mas_reaction_json_ribbon_base(ribbon_name, user_friendly_desc, helper_label):
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_ACS, ribbon_name)
        )
        _mas_gifted_ribbon_acs = mas_sprites.ACS_MAP.get(
            ribbon_name,
            mas_acs_ribbon_def
        )
        _mas_new_ribbon_color = user_friendly_desc

    call _mas_reaction_ribbon_helper(helper_label)

    python:
        # giftname is the 3rd item
        if sprite_data[2] is not None:
            store.mas_filereacts.delete_file(sprite_data[2])

        mas_finishSpriteObjInfo(sprite_data)
    return

# lanvallime

label mas_reaction_gift_acs_lanvallime_ribbon_coffee:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_coffee", "coffee colored", "mas_reaction_gift_acs_lanvallime_ribbon_coffee")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_gold:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_gold", "gold", "mas_reaction_gift_acs_lanvallime_ribbon_gold")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_hot_pink:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_hot_pink", "hot pink", "mas_reaction_gift_acs_lanvallime_ribbon_hot_pink")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_lilac:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_lilac", "lilac", "mas_reaction_gift_acs_lanvallime_ribbon_lilac")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_lime_green:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_lime_green", "lime green", "mas_reaction_gift_acs_lanvallime_lime_green")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_navy_blue:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_navy_blue", "navy", "mas_reaction_gift_acs_lanvallime_ribbon_navy_blue")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_orange:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_orange", "orange", "mas_reaction_gift_acs_lanvallime_ribbon_orange")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_royal_purple:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_royal_purple", "royal purple", "mas_reaction_gift_acs_lanvallime_ribbon_royal_purple")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_sky_blue:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_sky_blue", "sky blue", "mas_reaction_gift_acs_lanvallime_ribbon_sky_blue")
    return

# anonymioo
label mas_reaction_gift_acs_anonymioo_ribbon_bisexualpride:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_bisexualpride","bisexual-pride-themed","mas_reaction_gift_acs_anonymioo_ribbon_bisexualpride")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_blackandwhite:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_blackandwhite","black and white","mas_reaction_gift_acs_anonymioo_ribbon_blackandwhite")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_bronze:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_bronze","bronze","mas_reaction_gift_acs_anonymioo_ribbon_bronze")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_brown:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_brown","brown","mas_reaction_gift_acs_anonymioo_ribbon_brown")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_gradient:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_gradient","multi-colored","mas_reaction_gift_acs_anonymioo_ribbon_gradient")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_gradient_lowpoly:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_gradient_lowpoly","multi-colored","mas_reaction_gift_acs_anonymioo_ribbon_gradient_lowpoly")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_gradient_rainbow:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_gradient_rainbow","rainbow colored","mas_reaction_gift_acs_anonymioo_ribbon_gradient_rainbow")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_polkadots_whiteonred:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_polkadots_whiteonred","red and white polka dotted","mas_reaction_gift_acs_anonymioo_ribbon_polkadots_whiteonred")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_starsky_black:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_starsky_black","night-sky-themed","mas_reaction_gift_acs_anonymioo_ribbon_starsky_black")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_starsky_red:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_starsky_red","night-sky-themed","mas_reaction_gift_acs_anonymioo_ribbon_starsky_red")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_striped_blueandwhite:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_striped_blueandwhite","blue and white striped","mas_reaction_gift_acs_anonymioo_ribbon_striped_blueandwhite")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_striped_pinkandwhite:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_striped_pinkandwhite","pink and white striped","mas_reaction_gift_acs_anonymioo_ribbon_striped_pinkandwhite")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_transexualpride:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_transexualpride","transgender-pride-themed","mas_reaction_gift_acs_anonymioo_ribbon_transexualpride")
    return

# velius94

label mas_reaction_gift_acs_velius94_ribbon_platinum:
    call mas_reaction_json_ribbon_base("velius94_ribbon_platinum", "platinum", "mas_reaction_gift_acs_velius94_ribbon_platinum")
    return

label mas_reaction_gift_acs_velius94_ribbon_pink:
    call mas_reaction_json_ribbon_base("velius94_ribbon_pink", "pink", "mas_reaction_gift_acs_velius94_ribbon_pink")
    return

label mas_reaction_gift_acs_velius94_ribbon_peach:
    call mas_reaction_json_ribbon_base("velius94_ribbon_peach", "peach", "mas_reaction_gift_acs_velius94_ribbon_peach")
    return

label mas_reaction_gift_acs_velius94_ribbon_green:
    call mas_reaction_json_ribbon_base("velius94_ribbon_green", "green", "mas_reaction_gift_acs_velius94_ribbon_green")
    return

label mas_reaction_gift_acs_velius94_ribbon_emerald:
    call mas_reaction_json_ribbon_base("velius94_ribbon_emerald", "emerald", "mas_reaction_gift_acs_velius94_ribbon_emerald")
    return

label mas_reaction_gift_acs_velius94_ribbon_gray:
    call mas_reaction_json_ribbon_base("velius94_ribbon_gray", "gray", "mas_reaction_gift_acs_velius94_ribbon_gray")
    return

label mas_reaction_gift_acs_velius94_ribbon_blue:
    call mas_reaction_json_ribbon_base("velius94_ribbon_blue", "blue", "mas_reaction_gift_acs_velius94_ribbon_blue")
    return

label mas_reaction_gift_acs_velius94_ribbon_def:
    call mas_reaction_json_ribbon_base("velius94_ribbon_def", "white", "mas_reaction_gift_acs_velius94_ribbon_def")
    return

label mas_reaction_gift_acs_velius94_ribbon_black:
    call mas_reaction_json_ribbon_base("velius94_ribbon_black", "black", "mas_reaction_gift_acs_velius94_ribbon_black")
    return

label mas_reaction_gift_acs_velius94_ribbon_dark_purple:
    call mas_reaction_json_ribbon_base("velius94_ribbon_dark_purple", "dark purple", "mas_reaction_gift_acs_velius94_ribbon_dark_purple")
    return

label mas_reaction_gift_acs_velius94_ribbon_yellow:
    call mas_reaction_json_ribbon_base("velius94_ribbon_yellow", "yellow", "mas_reaction_gift_acs_velius94_ribbon_yellow")
    return

label mas_reaction_gift_acs_velius94_ribbon_red:
    call mas_reaction_json_ribbon_base("velius94_ribbon_red", "red", "mas_reaction_gift_acs_velius94_ribbon_red")
    return

label mas_reaction_gift_acs_velius94_ribbon_sapphire:
    call mas_reaction_json_ribbon_base("velius94_ribbon_sapphire", "sapphire", "mas_reaction_gift_acs_velius94_ribbon_sapphire")
    return

label mas_reaction_gift_acs_velius94_ribbon_teal:
    call mas_reaction_json_ribbon_base("velius94_ribbon_teal", "teal", "mas_reaction_gift_acs_velius94_ribbon_teal")
    return

label mas_reaction_gift_acs_velius94_ribbon_silver:
    call mas_reaction_json_ribbon_base("velius94_ribbon_silver", "silver", "mas_reaction_gift_acs_velius94_ribbon_silver")
    return

label mas_reaction_gift_acs_velius94_ribbon_light_purple:
    call mas_reaction_json_ribbon_base("velius94_ribbon_light_purple", "light purple", "mas_reaction_gift_acs_velius94_ribbon_light_purple")
    return

label mas_reaction_gift_acs_velius94_ribbon_ruby:
    call mas_reaction_json_ribbon_base("velius94_ribbon_ruby", "ruby", "mas_reaction_gift_acs_velius94_ribbon_ruby")
    return

label mas_reaction_gift_acs_velius94_ribbon_wine:
    call mas_reaction_json_ribbon_base("velius94_ribbon_wine", "wine colored", "mas_reaction_gift_acs_velius94_ribbon_wine")
    return

#specific to this, since we need to verify if the player actually gave a ribbon.
default persistent._mas_current_gifted_ribbons = 0

label _mas_reaction_ribbon_helper(label):
    #if we already have that ribbon
    if store.mas_selspr.get_sel_acs(_mas_gifted_ribbon_acs).unlocked:
        call mas_reaction_old_ribbon

    else:
        # since we don't have it we can accept it
        call mas_reaction_new_ribbon
        $ persistent._mas_current_gifted_ribbons += 1

    # normal gift processing
    $ mas_receivedGift(label)
    $ gift_ev_cat = mas_getEVLPropValue(label, "category")
    # for regular ribbons
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    #we have dlg for repeating ribbons, may as well have it used
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)

    return

label mas_reaction_new_ribbon:
    python:
        def _ribbon_prepare_hair():
            #If current hair doesn't support ribbons, we should change hair
            if not monika_chr.hair.hasprop("ribbon"):
                monika_chr.change_hair(mas_hair_def, False)

    $ mas_giftCapGainAff(3)
    if persistent._mas_current_gifted_ribbons == 0:
        m 1suo "Новая ленточка!"
        m 3hub "...и он [_mas_new_ribbon_color]!"

        #Ironically green is closer to her eyes, but given the selector dlg, we'll say this for both.
        if _mas_new_ribbon_color == "green" or _mas_new_ribbon_color == "emerald":
            m 1tub "...Прямо как мои глаза!"

        m 1hub "Большое спасибо [player], мне очень нравится!"
        if store.seen_event("monika_date"):
            m 3eka "Ты подарил это мне, потому что я упоминала, как люблю покупать юбки и бантики?"

            if mas_isMoniNormal(higher=True):
                m 3hua "Ты всегда такой заботливый~"

        m 3rksdlc "У меня действительно нет большого выбора здесь, когда дело доходит до моды..."
        m 3eka "...поэтому возможность изменить цвет моей ленты - это такая приятная мелочь."
        m 2dsa "На самом деле, я надену ее прямо сейчас.{w=0.5}.{w=0.5}.{nw}"
        $ store.mas_selspr.unlock_acs(_mas_gifted_ribbon_acs)
        $ _ribbon_prepare_hair()
        $ monika_chr.wear_acs(_mas_gifted_ribbon_acs)
        m 1hua "О, это замечательно, [player]!"

        if mas_isMoniAff(higher=True):
            m 1eka "Ты всегда заставляешь меня чувствовать себя такой любимой..."
        elif mas_isMoniHappy():
            m 1eka "Ты всегда знаешь, как сделать меня счастливой..."
        m 3hua "Ещё раз спасибо~"

    else:
        m 1suo "Ещё одна лента!"
        m 3hub "...И на этот раз [_mas_new_ribbon_color]!"

        #Ironically green is closer to her eyes, but given the selector dlg, we'll say this for both.
        if _mas_new_ribbon_color == "green" or _mas_new_ribbon_color == "emerald":
            m 1tub "...Прямо как мои глаза!"

        m 2dsa "Я надену это прямо сейчас.{w=0.5}.{w=0.5}.{nw}"
        $ store.mas_selspr.unlock_acs(_mas_gifted_ribbon_acs)
        $ _ribbon_prepare_hair()
        $ monika_chr.wear_acs(_mas_gifted_ribbon_acs)
        m 3hua "Большое спасибо [player], мне очень нравится!"
    return

label mas_reaction_old_ribbon:
    m 1rksdla "[player]..."
    m 1hksdlb "Ты уже подарил мне [mas_a_an_str(_mas_new_ribbon_color)] ленту!"
    return

init 5 python:
    addReaction("mas_reaction_gift_roses", "roses", is_good=True, exclude_on=["d25g"])

default persistent._date_last_given_roses = None

label mas_reaction_gift_roses:
    python:
        gift_ev_cat = mas_getEVLPropValue("mas_reaction_gift_roses", "category")
        if not mas_isO31():
            monika_chr.wear_acs(mas_acs_roses)

    #TODO: future migrate this to use history (post f14)
    if not persistent._date_last_given_roses and not renpy.seen_label('monika_valentines_start'):
        $ mas_giftCapGainAff(10)

        m 1eka "[player]... Я-я не знаю, что сказать..."
        m 1ekbsb "Я никогда бы не подумала, что ты подаришь мне что-то подобное!"
        m 3skbsa "Я так счастлива сейчас."
        if mas_isF14():
            # extra 5 points if f14
            $ mas_f14CapGainAff(5)
            m 3ekbsa "Подумать только, что я получу от тебя розы в День Святого Валентина..."
            m 1ekbsu "Ты такой милый."
            m 1dktpu "..."
            m 1ektda "А-ха-ха..."

        #We can only have this on poses which use the new sprite set
        if not monika_chr.is_wearing_clothes_with_exprop("baked outfit"):
            m 2dsa "Подожди.{w=0.5}.{w=0.5}.{nw}"
            $ monika_chr.wear_acs(mas_acs_ear_rose)
            m 1hub "Э-хе-хе, вот! Разве это не выглядит красиво на мне?"

        if mas_shouldKiss(chance=2, special_day_bypass=True):
            call monika_kissing_motion_short

    else:
        if persistent._date_last_given_roses is None and renpy.seen_label('monika_valentines_start'):
            $ persistent._date_last_given_roses = datetime.date(2018,2,14)

        if mas_pastOneDay(persistent._date_last_given_roses):
            $ mas_giftCapGainAff(5 if mas_isSpecialDay() else 1)

            m 1suo "OО!"
            m 1ekbsa "Спасибо, [player]."
            m 3ekbsa "Мне всегда нравится получать от тебя розы."
            if mas_isF14():
                # extra 5 points if f14
                $ mas_f14CapGainAff(5)
                m 1dsbsu "Особенно в такой день, как сегодня."
                m 1ekbsa "Это очень мило с твоей стороны, что ты подарил их мне."
                m 3hkbsa "Я так тебя люблю."
                m 1ekbsa "С Днём Святого Валентина, [player]~"
            else:
                m 1ekbsa "Ты всегда такой милый."

            #Random chance (unless f14) for her to do the ear rose thing
            if (
                not monika_chr.is_wearing_acs_with_mux("left-hair-flower-ear")
                and (
                    (mas_isSpecialDay() and renpy.random.randint(1,2) == 1)
                    or renpy.random.randint(1,4) == 1
                    or mas_isF14()
                    or mas_isO31()
                )
            ):
                m 2dsa "Подожди.{w=0.5}.{w=0.5}.{nw}"
                $ monika_chr.wear_acs(mas_acs_ear_rose)
                m 1hub "Э-хе-хе~"

            if mas_shouldKiss(chance=4, special_day_bypass=True):
                call monika_kissing_motion_short

        else:
            m 1hksdla "[player], я польщена, правда, но тебе не нужно дарить мне столько роз."
            if store.seen_event("monika_clones"):
                m 1ekbsa "В конце концов, ты всегда будешь моей особенной розой, э-хе-хе~"
            else:
                m 1ekbsa "Одна роза от тебя - это уже больше, чем я когда-либо могла просить."

    # Pop from reacted map
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    $ persistent._date_last_given_roses = datetime.date.today()

    # normal gift processing
    $ mas_receivedGift("mas_reaction_gift_roses")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    return


init 5 python:
    addReaction("mas_reaction_gift_chocolates", "chocolates", is_good=True, exclude_on=["d25g"])

default persistent._given_chocolates_before = False

label mas_reaction_gift_chocolates:
    $ gift_ev_cat = mas_getEVLPropValue("mas_reaction_gift_chocolates", "category")

    if not persistent._mas_given_chocolates_before:
        $ persistent._mas_given_chocolates_before = True

        #If we're eating something already, that takes priority over the acs
        if not MASConsumable._getCurrentFood() and not mas_isO31():
            $ monika_chr.wear_acs(mas_acs_heartchoc)

        $ mas_giftCapGainAff(5)

        m 1tsu "Это так {i}мило{/i} с твоей стороны, эхехе~"
        if mas_isF14():
            #Extra little bump if on f14
            $ mas_f14CapGainAff(5)
            m 1ekbsa "Дарить мне шоколад в День Святого Валентина..."
            m 1ekbfa "Ты действительно знаешь, как заставить девушку почувствовать себя особенной, [player]."
            if renpy.seen_label('monika_date'):
                m 1lkbfa "Я знаю, что упоминала, что когда-нибудь мы вместе посетим шоколадный магазин..."
                m 1hkbfa "Но пока мы не можем этого сделать, а получить шоколадные конфеты в подарок от тебя..."
            m 3ekbfa "Это много значит - получить их от тебя."

        elif renpy.seen_label('monika_date') and not mas_isO31():
            m 3rka "Я знаю, что упоминала, что когда-нибудь мы вместе посетим шоколадный магазин..."
            m 3hub "Но пока мы не можем этого сделать, получить от тебя в подарок шоколадные конфеты значит для меня всё."
            m 1ekc "Мне бы очень хотелось, чтобы мы могли ими поделиться..."
            m 3rksdlb "Но пока этот день не настал, мне придется наслаждаться ими за нас обоих, а-ха-ха!"
            m 3hua "Спасибо, [mas_get_player_nickname()]~"

        else:
            m 3hub "Я люблю шоколад!"
            m 1eka "И получить от тебя несколько штук для меня многое значит."
            m 1hub "Спасибо, [player]!"

    else:
        $ times_chocs_given = mas_getGiftStatsForDate("mas_reaction_gift_chocolates")
        if times_chocs_given == 0:
            #We want this to show up where she accepts the chocs
            #Same as before, we don't want these to show up if we're already eating
            if not MASConsumable._getCurrentFood():
                #If we have the plush out, we should show the middle one here
                if not (mas_isF14() or mas_isD25Season()):
                    if monika_chr.is_wearing_acs(mas_acs_quetzalplushie):
                        $ monika_chr.wear_acs(mas_acs_center_quetzalplushie)

                else:
                    $ monika_chr.remove_acs(store.mas_acs_quetzalplushie)

                if not mas_isO31():
                    $ monika_chr.wear_acs(mas_acs_heartchoc)

            $ mas_giftCapGainAff(3 if mas_isSpecialDay() else 1)

            m 1wuo "О!"

            if mas_isF14():
                #Extra little bump if on f14
                $ mas_f14CapGainAff(5)
                m 1eka "[player]!"
                m 1ekbsa "Ты такой милый, даришь мне шоколад в такой день, как сегодня..."
                m 1ekbfa "Ты действительно знаешь, как заставить меня чувствовать себя особенной."
                m "Спасибо, [player]."
            else:
                m 1hua "Спасибо за шоколадки, [player]!"
                m 1ekbsa "Каждый кусочек напоминает мне о том, какой ты милый, э-хе-хе~"

        elif times_chocs_given == 1:
            #Same here
            if not MASConsumable._getCurrentFood() and not mas_isO31():
                $ monika_chr.wear_acs(mas_acs_heartchoc)

            m 1eka "Ещё шоколада, [player]?"
            m 3tku "Ты действительно любишь баловать меня, не так ли,{w=0.2} {nw}"
            extend 3tub "а-ха-ха!"
            m 1rksdla "Я всё ещё не доела первую коробку, которую ты мне подарил..."
            m 1hub "...но я не жалуюсь!"

        elif times_chocs_given == 2:
            m 1ekd "[player]..."
            m 3eka "Думаю, сегодня ты дал мне достаточно шоколадок."
            m 1rksdlb "Три коробки - это слишком много, а я еще даже не доела первую!"
            m 1eka "Оставь их на другой раз, хорошо?"

        else:
            m 2tfd "[player]!"
            m 2tkc "Я уже сказала тебе, что мне хватит шоколадок на один день, но ты продолжаешь пытаться дать мне ещё больше..."
            m 2eksdla "Пожалуйста...{w=1}просто оставь их на другой день."

    #If we're wearing the chocs, we'll remove them here
    if monika_chr.is_wearing_acs(mas_acs_heartchoc):
        call mas_remove_choc

    #pop from reacted map
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    # normal gift processing
    $ mas_receivedGift("mas_reaction_gift_chocolates")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    return

label mas_remove_choc:
    # we remove chocolates if not f14
    m 1hua "..."
    m 3eub "Они {i}очень{/i} вкусные!"
    m 1hua "..."
    m 3hksdlb "А-ха-ха! Наверное, мне стоит их пока убрать..."
    m 1rksdla "Если я оставлю их здесь надолго, то не останется ничего, чтобы насладиться ими позже!"

    call mas_transition_to_emptydesk

    python:
        renpy.pause(1, hard=True)
        monika_chr.remove_acs(mas_acs_heartchoc)
        renpy.pause(3, hard=True)

    call mas_transition_from_emptydesk("monika 1eua")

    #Now move the plush
    if monika_chr.is_wearing_acs(mas_acs_center_quetzalplushie):
        $ monika_chr.wear_acs(mas_acs_quetzalplushie)

    m 1eua "Так что ещё ты хотел сделать сегодня"
    return

label mas_reaction_gift_clothes_orcaramelo_bikini_shell:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "orcaramelo_bikini_shell")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1sua "О! {w=0.5}Бикини с ракушками!"
    m 1hub "Спасибо, [mas_get_player_nickname()]!{w=0.5} I'm going to try it on right now!"

    # try it on
    call mas_clothes_change(sprite_object)

    m 2ekbfa "Ну...{w=0.5} Что ты думаешь?"
    m 2hubfa "Я похожа на русалку? Э-хе-хе."
    show monika 5ekbfa at i11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbfa "Я думаю, это очень мило, [player]..."
    m 5hubfa "Надо будет как-нибудь сходить на пляж!"

    if mas_isWinter() or mas_isMoniNormal(lower=True):
        if mas_isWinter():
            show monika 2rksdla at i11 zorder MAS_MONIKA_Z with dissolve_monika
            m 2rksdla "...Но пока что здесь немного прохладно..."
            m 2eka "Так что я пойду надену что-нибудь потеплее..."

        elif mas_isMoniNormal(lower=True):
            show monika 2hksdlb at i11 zorder MAS_MONIKA_Z with dissolve_monika
            m 2hksdlb "А-ха-ха..."
            m 2rksdla "Немного неловко сидеть вот так перед тобой."
            m 2eka "Надеюсь, ты не возражаешь, но я пойду переоденусь..."

        # change to def normally, santa during d25 outfit season
        $ clothes = mas_clothes_def
        if persistent._mas_d25_in_d25_mode and mas_isD25Outfit():
            $ clothes = mas_clothes_santa
        call mas_clothes_change(clothes)

        m 2eua "Ах, так лучше..."
        m 3hua "Ещё раз спасибо за чудесный подарок~"


    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_acs_orcaramelo_hairflower_pink:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_ACS, "orcaramelo_hairflower_pink")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(1)

    m 3sua "О!{w=0.5} Какой милый маленький цветочек!"
    m 1ekbsa "Спасибо [player], ты такой милый~"
    m 1dua "Подожди.{w=0.5}.{w=0.5}.{nw}"
    $ monika_chr.wear_acs(sprite_object)
    m 1hua "Э-хе-хе~"
    m 1hub "Ещё раз спасибо, [player]!"

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_velius94_shirt_pink:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "velius94_shirt_pink")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1suo "Боже мой!"
    m 1suo "Она {i}такая{/i} красивая!"
    m 3hub "Большое спасибо, [player]!"
    m 3eua "Подожди, дай-ка я быстренько примерю..."

    # try it on
    call mas_clothes_change(sprite_object)

    m 2sub "Аах, отлично сидит!"
    m 3hub "Мне тоже очень нравятся цвета! Розовый и черный так хорошо сочетаются."
    m 3eub "Не говоря уже о том, что юбка выглядит очень мило с этими узорами!"
    m 2tfbsd "И все же по какой-то причине я не могу отделаться от ощущения, что твои глаза как бы дрейфуют...{w=0.5}кхм...{w=0.5}{i}в другом месте{/i}."

    if mas_selspr.get_sel_clothes(mas_clothes_sundress_white).unlocked:
        m 2lfbsp "Я же говорила тебе, что пялиться невежливо, [player]."
    else:
        m 2lfbsp "Невежливо пялиться, понимаешь?"

    m 2hubsb "А-ха-ха!"
    m 2tkbsu "Расслабься, расслабься...{w=0.5}просто дразню тебя~"
    m 3hub "Ещё раз большое спасибо за этот наряд, [player]!"

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_orcaramelo_sakuya_izayoi:

    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "orcaramelo_sakuya_izayoi")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1sub "О! {w=0.5}Это..."
    m 2euc "Наряд горничной?"
    m 3tuu "Э-хе-хе~"
    m 3tubsb "Знаешь, если тебе нравятся такие вещи, ты мог бы просто сказать мне..."
    m 1hub "А-ха-ха! Просто шучу~"
    m 1eub "Пойду-ка я его надену!"

    # try it on
    call mas_clothes_change(sprite_object, outfit_mode=True)

    m 2hua "Итак,{w=0.5} как я выгляжу?"
    m 3eub "Мне кажется, что я успею сделать все, что угодно, прежде чем ты успеешь моргнуть."
    m 1eua "...Пока ты не отвлекаешь меня слишком сильно, э-хе-хе~"
    m 1lkbfb "Я бы всё ещё хотела иметь возможность проводить с тобой время, масте--{nw}"
    $ _history_list.pop()
    m 1ekbfb "Я бы всё ещё хотела иметь возможность проводить с тобой время,{fast} [player]."

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_finale_jacket_brown:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "finale_jacket_brown")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1sub "О!{w=0.5} Зимний пиджак!"
    m 1suo "И к ней даже прилагается шарф!"
    if mas_isSummer():
        m 3rksdlu "...Хотя мне становится немного жарко от одного взгляда на нее, а-ха-ха..."
        m 3eksdla "Возможно, лето - не лучшее время, чтобы носить это, [player]."
        m 3eka "Я ценю эту мысль, и я с удовольствием надену его через несколько месяцев."

    else:
        if mas_isWinter():
            m 1tuu "Благодаря тебе, я никогда не замерзну в ближайшее время, [player]~"
        m 3eub "Дай мне пойти надеть его! Я сейчас вернусь."

        # try it on
        call mas_clothes_change(sprite_object)

        m 2dku "Ахх, это очень приятн~"
        m 1eua "Мне нравится, как оно на мне смотрится, ты согласен?"
        if mas_isMoniNormal(higher=True):
            m 3tku "Ну... Я не могу ожидать от тебя объективности в этом вопросе, не так ли?"
            m 1hubfb "А-ха-ха!"
        m 1ekbfa "Спасибо [player], мне нравится."

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_orcaramelo_sweater_shoulderless:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "orcaramelo_sweater_shoulderless")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1sub "О!{w=0.5} Свитер!"
    m 1hub "И выглядит так уютно!"
    if mas_isWinter():
        m 2eka "Ты такой заботливый [player], подарив мне это в такой холодный зимний день..."
    m 3eua "Дай-ка я его примерю."

    # try it on
    call mas_clothes_change(sprite_object)

    m 2dkbsu "это так...{w=1}удобно. Я чувствую себя уютно, как жук в ковре. Э-хе-хе~"
    m 1ekbsa "Спасибо, [player]. Мне нравится!"
    m 3hubsb "еперь всякий раз, когда я его надеваю, я буду думать о твоем тепле. А-ха-ха~"

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_velius94_dress_whitenavyblue:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "velius94_dress_whitenavyblue")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1suo "Боже мой!"
    m 1sub "Это платье великолепно, [player]!"
    m 3hub "Я собираюсь примерить его прямо сейчас!"

    # try it on
    call mas_clothes_change(sprite_object, outfit_mode=True)

    m "Итак,{w=0.5} что ты делаешь?"
    m 3eua "Я думаю, что этот оттенок синего очень хорошо сочетается с белым."
    $ scrunchie = monika_chr.get_acs_of_type('bunny-scrunchie')

    if scrunchie and scrunchie.name == "velius94_bunnyscrunchie_blue":
        m 3eub "И кроличий бантик прекрасно дополняет наряд!"
    m 1eka "Большое спасибо, [player]."

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_mocca_bun_blackandwhitestripedpullover:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "mocca_bun_blackandwhitestripedpullover")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1sub "О, новая одежда!"
    m 3hub "Выглядит потрясающе, [player]!"
    m 3eua "Секундочку, дай-ка я ее надену.{w=0.3}.{w=0.3}.{w=0.3}{nw}"
    call mas_clothes_change(sprite_object)

    m 2eua "Ну, что ты думаешь?"
    m 7hua "Я думаю, что это выглядит довольно мило на мне.{w=0.2} {nw}"
    extend 3rubsa " определенно приберегу этот наряд для свидания~"
    m 1hub "Ещё раз спасибо, [player]!"

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

init 5 python:
    # TODO: Add a way to generalize this
    if not mas_seenEvent("mas_reaction_gift_noudeck"):
        addReaction("mas_reaction_gift_noudeck", "noudeck", is_good=True)

label mas_reaction_gift_noudeck:
    python:
        mas_giftCapGainAff(0.5)
        # She keeps the deck at any aff
        mas_unlockGame("nou")
        mas_unlockEVL("monika_explain_nou_rules", "EVE")

    if mas_isMoniNormal(higher=True):
        m 1wub "О!{w=0.3} Колода карт!"
        m 3eua "И мне кажется, я знаю, как играть в эту игру!"
        m 1esc "Я слышала, что она может {i}влиять{/i} на твои отношения с людьми, с которыми ты играешь."

        if mas_isMoniAff(higher=True):
            show monika 5eubsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eubsa "Но я знаю, что наши отношения могут выдержать гораздо больше, чем простая карточная игра~"
            m 5hubsa "Э-хе-хе~"
            show monika 1eua at t11 zorder MAS_MONIKA_Z with dissolve_monika

        else:
            m 1hub "А-ха-ха!"
            m 1eua "Я просто шучу, [player]."

        m 1eua "Ты когда-нибудь играл в  'NOU', [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты когда-нибудь играл в  'NOU', [player]?{fast}"

            # If you're an advanced nou'r, we unlock house rules for you from the start
            "Да.":
                m 1rksdlb "А-ха-ха..."
                m 1eksdla "Конечно, да, ты же подарил мне колоду, в конце концов."
                call mas_reaction_gift_noudeck_have_played

            "Нет.":
                m 3tuu "Тогда как насчет 'UNO', э-хе-хе?{nw}"
                $ _history_list.pop()
                menu:
                    m "Тогда как насчет 'UNO', э-хе-хе?{fast}"

                    "Да.":
                        m 3hub "Отлично! {w=0.3}{nw}"
                        extend 3tub "'NOU' это {i}очень{/i} похожее на это, а-ха-ха..."
                        call mas_reaction_gift_noudeck_have_played

                    "Нет.":
                        call mas_reaction_gift_noudeck_havent_played

        m 3hub "Не могу дождаться, чтобы поиграть с тобой!!"

    elif mas_isMoniDis(higher=True):
        m 2euc "Колода?"
        m 2rka "Вообще-то это может быть...{nw}"
        $ _history_list.pop()
        m 2rkc "Неважно.."
        m 2esc "Я сейчас не в настроении играть, [player]."

    else:
        m 6ckc "..."

    python:
        mas_receivedGift("mas_reaction_gift_noudeck")
        gift_ev = mas_getEV("mas_reaction_gift_noudeck")
        if gift_ev:
            store.mas_filereacts.delete_file(gift_ev.category)

    return

label mas_reaction_gift_noudeck_havent_played:
    m 1eka "Ох, все в порядке."
    m 4eub "Это популярная карточная игра, в которой для победы нужно разыграть все свои карты раньше соперников."
    m 1rssdlb "Это может показаться очевидным, а-ха-ха~"
    m 3eub "Но это действительно веселая игра, в которую можно играть с друзьями и близкими~"
    m 1eua "Я объясню тебе основные правила позже, просто спроси."
    return

label mas_reaction_gift_noudeck_have_played:
    m 1eua "Ты, наверное, уже знаешь, что некоторые люди играют по своим правилам."
    m 3eub "И если ты хочешь, мы тоже можем установить свои правила."
    m 3eua "Или же, если ты не помнишь правила, я всегда могу напомнить тебе, просто спроси."
    python:
        mas_unlockEVL("monika_change_nou_house_rules", "EVE")
        persistent._seen_ever["monika_introduce_nou_house_rules"] = True
        persistent._seen_ever["monika_explain_nou_rules"] = True
    return
