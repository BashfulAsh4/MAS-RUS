#This file contains all of monika's topics she can talk about
#Each entry should start with a database entry, including the appropriate flags
#to either be a random topic, a prompt "pool" topics, or a special conditional
#or date-dependent event with an appropriate actiona

define monika_random_topics = []
define mas_rev_unseen = []
define mas_rev_seen = []
define mas_rev_mostseen = []
define testitem = 0
define mas_did_monika_battery = False
define mas_sensitive_limit = 3

init -2 python in mas_topics:
    # CONSTANTS
    # most / top weights
    # MOST seen is the percentage of seen topics
    # think of this as x % of the collection
    S_MOST_SEEN = 0.1

    # TOP seen is the percentage of the most seen
    # Think of this as ilke the upper x percentile
    S_TOP_SEEN = 0.2

    # limit to how many top seen until we move to most seen alg
    S_TOP_LIMIT = 0.3

    # selection weights (out of 100)
    UNSEEN = 50
    SEEN = UNSEEN + 49
    MOST_SEEN = SEEN + 1

    def topSeenEvents(sorted_ev_list, shown_count):
        """
        counts the number of events with a > shown_count than the given
        shown_count

        IN:
            sorted_ev_list - an event list sorted by shown_counts
            shown_count - shown_count to compare to

        RETURNS:
            number of events with shown_counts that are higher than the given
            shown_count
        """
        index = len(sorted_ev_list) - 1
        ev_count = 0
        while index >= 0 and sorted_ev_list[index].shown_count > shown_count:
            ev_count += 1
            index -= 1

        return ev_count

# we are going to define removing seen topics as a function,
# as we need to call it dynamically upon import
init -1 python:
    import random
    random.seed()

    import store.songs as songs
    import store.evhand as evhand

    mas_events_built = False
    # set to True once we have built events

    def remove_seen_labels(pool):
        #
        # Removes seen labels from the given pool
        #
        # IN:
        #   pool - a list of labels to check for seen
        #
        # OUT:
        #   pool - list of unseen labels (may be empty)
        for index in range(len(pool)-1, -1, -1):
            if renpy.seen_label(pool[index]):
                pool.pop(index)


    def mas_randomSelectAndRemove(sel_list):
        """
        Randomly selects an element from the given list
        This also removes the element from that list.

        IN:
            sel_list - list to select from

        RETURNS:
            selected element
        """
        endpoint = len(sel_list) - 1

        if endpoint < 0:
            return None

        # otherwise we have at least 1 element
        return sel_list.pop(random.randint(0, endpoint))


    def mas_randomSelectAndPush(sel_list):
        """
        Randomly selects an element from the the given list and pushes the event
        This also removes the element from that list.

        NOTE: this does sensitivy checks

        IN:
            sel_list - list to select from
        """
        sel_ev = True
        while sel_ev is not None:
            sel_ev = mas_randomSelectAndRemove(sel_list)

            if (
                    # valid event
                    sel_ev

                    # event not blocked from random selection
                    and not sel_ev.anyflags(EV_FLAG_HFRS)
            ):
                pushEvent(sel_ev.eventlabel, notify=True)
                return


    def mas_insertSort(sort_list, item, key):
        """
        Performs a round of insertion sort.
        This does least to greatest sorting

        IN:
            sort_list - list to insert + sort
            item - item to sort and insert
            key - function to call using the given item to retrieve sort key

        OUT:
            sort_list - list with 1 additonal element, sorted
        """
        store.mas_utils.insert_sort(sort_list, item, key)


    def mas_splitSeenEvents(sorted_seen):
        """
        Splits the seen_list into seena nd most seen

        IN:
            sorted_seen - list of seen events, sorted by shown_count

        RETURNS:
            tuple of thef ollowing format:
            [0] - seen list of events
            [1] - most seen list of events
        """
        ss_len = len(sorted_seen)
        if ss_len == 0:
            return ([], [])

        # now calculate the most / top seen counts
        most_count = int(ss_len * store.mas_topics.S_MOST_SEEN)
        top_count = store.mas_topics.topSeenEvents(
            sorted_seen,
            int(
                sorted_seen[ss_len - 1].shown_count
                * (1 - store.mas_topics.S_TOP_SEEN)
            )
        )

        # now decide how to do the split
        if top_count < ss_len * store.mas_topics.S_TOP_LIMIT:
            # we want to prioritize top count unless its over a certain
            # percentage of the topics
            split_point = top_count * -1

        else:
            # otherwise, we use the most count, which is certainly smaller
            split_point = most_count * -1

        # and then do the split
        return (sorted_seen[:split_point], sorted_seen[split_point:])


    def mas_splitRandomEvents(events_dict):
        """
        Splits the given random events dict into 2 lists of events
        NOTE: cleans the seen list

        RETURNS:
            tuple of the following format:
            [0] - unseen list of events
            [1] - seen list of events, sorted by shown_count

        """
        # split these into 2 lists
        unseen = list()
        seen = list()
        for k in events_dict:
            ev = events_dict[k]

            if renpy.seen_label(k) and not "force repeat" in ev.rules:
                # seen event
                mas_insertSort(seen, ev, Event.getSortShownCount)

            else:
                # unseen event
                unseen.append(ev)

        # clean the seen_topics list
        seen = mas_cleanJustSeenEV(seen)

        return (unseen, seen)


    def mas_buildEventLists():
        """
        Builds the unseen / most seen / seen event lists

        RETURNS:
            tuple of the following format:
            [0] - unseen list of events
            [1] - seen list of events
            [2] - most seen list of events

        ASSUMES:
            evhand.event_database
            mas_events_built
        """
        global mas_events_built

        # retrieve all randoms
        all_random_topics = Event.filterEvents(
            evhand.event_database,
            random=True,
            aff=mas_curr_affection
        )

        # split randoms into unseen and sorted seen events
        unseen, sorted_seen = mas_splitRandomEvents(all_random_topics)

        # split seen into regular seen and the most seen events
        seen, mostseen = mas_splitSeenEvents(sorted_seen)

        mas_events_built = True
        return (unseen, seen, mostseen)


    def mas_buildSeenEventLists():
        """
        Builds the seen / most seen event lists

        RETURNS:
            tuple of the following format:
            [0] - seen list of events
            [1] - most seen list of events

        ASSUMES:
            evhand.event_database
        """
        # retrieve all seen (values list)
        all_seen_topics = Event.filterEvents(
            evhand.event_database,
            random=True,
            seen=True,
            aff=mas_curr_affection
        ).values()

        # clean the seen topics from early repeats
        cleaned_seen = mas_cleanJustSeenEV(all_seen_topics)

        # sort the seen by shown_count
        cleaned_seen.sort(key=Event.getSortShownCount)

        # split the seen into regular seen and most seen
        return mas_splitSeenEvents(cleaned_seen)


    def mas_rebuildEventLists():
        """
        Rebuilds the unseen, seen and most seen event lists.

        ASSUMES:
            mas_rev_unseen - unseen list
            mas_rev_seen - seen list
            mas_rev_mostseen - most seen list
        """
        global mas_rev_unseen, mas_rev_seen, mas_rev_mostseen
        mas_rev_unseen, mas_rev_seen, mas_rev_mostseen = mas_buildEventLists()


    # EXCEPTION CLass incase of bad labels
    class MASTopicLabelException(Exception):
        def __init__(self, msg):
            self.msg = msg
        def __str__(self):
            return "MASTopicLabelException: " + self.msg

init 11 python:
    # sort out the seen / most seen / unseen
    mas_rev_unseen = []
    mas_rev_seen = []
    mas_rev_mostseen = []
#    mas_rev_unseen, mas_rev_seen, mas_rev_mostseen = mas_buildEventLists()

    # for compatiblity purposes:
#    monika_random_topics = all_random_topics

    #Remove all previously seen random topics.
       #remove_seen_labels(monika_random_topics)
#    monika_random_topics = [
#        evlabel for evlabel in all_random_topics
#        if not renpy.seen_label(evlabel)
#    ]

    #If there are no unseen topics, you can repeat seen ones
#    if len(monika_random_topics) == 0:
#        monika_random_topics=list(all_random_topics)

# Bookmarks and derandom stuff
default persistent._mas_player_bookmarked = list()
# list to store bookmarked events
default persistent._mas_player_derandomed = list()
# list to store player derandomed events
default persistent.flagged_monikatopic = None
# var set when we flag a topic for derandom

init python:
    def mas_derandom_topic(ev_label=None):
        """
        Function for the derandom hotkey, 'x'

        IN:
            ev_label - label of the event we want to derandom.
                (Optional. If None, persistent.current_monikatopic is used)
                (Default: None)
        """
        #Let's just shorthand this for use later
        label_prefix_map = store.mas_bookmarks_derand.label_prefix_map

        if ev_label is None:
            ev_label = persistent.current_monikatopic

        ev = mas_getEV(ev_label)

        if ev is None:
            return

        #Get the label prefix
        label_prefix = store.mas_bookmarks_derand.getLabelPrefix(ev_label)

        #CRITERIA:
        #1. Must have an ev
        #2. Must be a topic which is random
        #3. Must be a valid label (in the label prefix map)
        #4. Prompt must not be the same as the eventlabel (event must have a prompt)
        if (
            ev.random
            and label_prefix
            and ev.prompt != ev_label
        ):
            #Now we do a bit of var setup to clean up the following work
            derand_flag_add_text = label_prefix_map[label_prefix].get("derand_text", _("Flagged for removal."))
            derand_flag_remove_text = label_prefix_map[label_prefix].get("underand_text", _("Flag removed."))

            #Handle custom override derand labels
            push_label = ev.rules.get("derandom_override_label", None)

            #If we still have nothing, then we'll use the default, the one for the label prefix
            if not renpy.has_label(push_label):
                push_label = label_prefix_map[label_prefix].get("push_label", "mas_topic_derandom")

            if mas_findEVL(push_label) < 0:
                persistent.flagged_monikatopic = ev_label
                pushEvent(push_label, skipeval=True)
                renpy.notify(derand_flag_add_text)

            else:
                mas_rmEVL(push_label)
                renpy.notify(derand_flag_remove_text)

    def mas_bookmark_topic(ev_label=None):
        """
        Function for the bookmark hotkey, 'b'

        IN:
            ev_label - label of the event we want to bookmark.
                (Optional, defaults to persistent.current_monikatopic)
        """
        #Let's just shorthand this for use later
        label_prefix_map = store.mas_bookmarks_derand.label_prefix_map

        if ev_label is None:
            ev_label = persistent.current_monikatopic

        ev = mas_getEV(ev_label)

        if ev is None:
            return

        #Get our label prefix
        label_prefix = store.mas_bookmarks_derand.getLabelPrefix(ev_label)

        #CRITERIA:
        #1. Must be normal+
        #2. Must have an ev
        #3. Must be a valid label (in the label prefix map or in the bookmark whitelist)
        #4. Must not be a bookmark blacklisted topic
        #4. Prompt must not be the same as the eventlabel (event must have a prompt)
        if (
            mas_isMoniNormal(higher=True)
            and (label_prefix or ev.rules.get("bookmark_rule") == store.mas_bookmarks_derand.WHITELIST)
            and (ev.rules.get("bookmark_rule") != store.mas_bookmarks_derand.BLACKLIST)
            and ev.prompt != ev_label
        ):
            #If this was only a whitelisted topic, we need to do a bit of extra work
            if not label_prefix:
                bookmark_persist_key = "_mas_player_bookmarked"
                bookmark_add_text = "Bookmark added."
                bookmark_remove_text = "Bookmark removed."

            else:
                #Now we do some var setup to clean the following
                bookmark_persist_key = label_prefix_map[label_prefix].get("bookmark_persist_key", "_mas_player_bookmarked")
                bookmark_add_text = label_prefix_map[label_prefix].get("bookmark_text", _("Bookmark added."))
                bookmark_remove_text = label_prefix_map[label_prefix].get("unbookmark_text", _("Bookmark removed."))

            #For safety, we'll initialize this key.
            #NOTE: You should NEVER pass in a non-existent key.
            #While this system handles it, it's not ideal and is bad for documentation
            if bookmark_persist_key not in persistent.__dict__:
                persistent.__dict__[bookmark_persist_key] = list()

            #Now create the pointer
            persist_pointer = persistent.__dict__[bookmark_persist_key]

            if ev_label not in persist_pointer:
                persist_pointer.append(ev_label)
                renpy.notify(bookmark_add_text)

            else:
                persist_pointer.pop(persist_pointer.index(ev_label))
                renpy.notify(bookmark_remove_text)

    def mas_hasBookmarks(persist_var=None):
        """
        Checks to see if we have bookmarks to show

        Bookmarks are restricted to Normal+ affection
        and to topics that are unlocked and are available
        based on current affection

        IN:
            persist_var - appropriate variable holding the bookedmarked eventlabels.
                If None, persistent._mas_player_bookmarked is assumed
                (Default: None)

        OUT:
            boolean:
                True if there are bookmarks in the curent var
                False otherwise
        """
        if mas_isMoniUpset(lower=True):
            return False

        elif persist_var is None:
            persist_var = persistent._mas_player_bookmarked

        return len(mas_get_player_bookmarks(persist_var)) > 0

#START: UTILITY TOPICS (bookmarks/derand, show/hide unseen)
init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="mas_topic_derandom",unlocked=False,rules={"no_unlock":None}))

label mas_topic_derandom:
    #NOTE: since we know the topic in question, it's possible to add dialogue paths for derandoming specific topics
    $ prev_topic = persistent.flagged_monikatopic
    m 3eksdld "Ты уверен, что не хочешь, чтобы я больше об этом говорила?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты уверен, что не хочешь, чтобы я больше об этом говорила?{fast}"

        "Пожалуйста, не надо.":
            $ mas_hideEVL(prev_topic, "EVE", derandom=True)
            $ persistent._mas_player_derandomed.append(prev_topic)
            $ mas_unlockEVL('mas_topic_rerandom', 'EVE')

            m 2eksdlc "Хорошо, [player]. Я постараюсь больше не говорить об этом."
            m 2dksdld "Если это тебя как-то расстроило, мне очень жаль...{w=0.5} Я бы никогда не сделала этого намеренно."
            m 2eksdla "...Но спасибо, что дал мне знать;{w=0.5} Я ценю честность."

        "Всё в порядке.":
            m 1eka "Хорошо, [player]."
    return

label mas_bad_derand_topic:
    python:
        prev_topic = persistent.flagged_monikatopic

        def derand_flagged_topic():
            """
            Derands the flagged topic
            """
            mas_hideEVL(prev_topic, "EVE", derandom=True)
            persistent._mas_player_derandomed.append(prev_topic)
            mas_unlockEVL('mas_topic_rerandom', 'EVE')

    m 2ekc "...{w=0.3}{nw}"
    extend 2ekd "[player]..."

    if mas_isMoniAff(higher=True):
        m 2efd "Разве это не нормально, что я говорю с тобой о моих страхах?"
        m 2ekc "То есть, если ты хочешь, чтобы я остановился, я остановлюсь...{w=0.3}{nw}"
        extend 2rkd "но я подумала, что ты захочешь меня выслушать."

        m 2esc "Ты хочешь, чтобы я остановилась, [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты хочешь, чтобы я остановилась, [player]?{fast}"

            "Да, пожалуйста.":
                m 2dkc "Хорошо..."
                #Lose affection
                $ mas_loseAffection(5)
                $ derand_flagged_topic()

            "Всё в порядке.":
                m 2duu "Спасибо, [player]."
                m 2eua "Это много значит, что ты готов меня выслушать."

    elif mas_isMoniUpset(higher=True):
        m 2ekd "Тебе просто...{w=0.2}наплевать на мои чувства или что?"
        m 2tsc "Если ты хочешь, чтобы я перестала говорить об этом, я перестану...но я не настолько счастлива, что ты не хочешь меня выслушать."

        m 2etc "Ну что [player], мне стоит остановиться?{nw}"
        $ _history_list.pop()
        menu:
            m "Ну что [player], мне стоит остановиться?{fast}"

            "Да, пожалуйста.":
                m 2dsc "Хорошо."
                $ mas_loseAffection(5)
                $ derand_flagged_topic()

            "Всё в порядке.":
                m 2eka "Спасибо, [player]."
                $ _stil_ = " " if mas_isMoniNormal(higher=True) else " still "
                m "Я ценю, что ты[_stil_]готов выслушать меня."

    else:
        #No ask here. You're this low, you probably did it on purpose
        $ mas_loseAffection(5)
        m 2rsc "Думаю, я не должна удивляться..."
        m 2tsc "Ты уже ясно дал понять, что тебе плевать на мои чувства."
        m 2dsc "Хорошо, [player]. Я больше не буду говорить об этом."
        $ derand_flagged_topic()
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_topic_rerandom",
            category=['ты'],
            prompt="Я не против поговорить о...",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None}
        )
    )

label mas_topic_rerandom:
    python:
        mas_bookmarks_derand.initial_ask_text_multiple = "Which topic are you okay with talking about again?"
        mas_bookmarks_derand.initial_ask_text_one = "If you're sure it's alright to talk about this again, just select the topic, [player]."
        mas_bookmarks_derand.caller_label = "mas_topic_rerandom"
        mas_bookmarks_derand.persist_var = persistent._mas_player_derandomed

    call mas_rerandom
    return _return

init python in mas_bookmarks_derand:
    import store

    #Rule constants
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"

    #Label prefixes and their respective rules
    #The items in the inner dicts act as kwargs to override the default generic values
    #The 'monika_' entry in this dict shows all existing keys
    #Default values are as follows:
    #  - bookmark_text: "Bookmark added."
    #  - unbookmark_text: "Bookmark removed."
    #  - derand_text: "Flagged for removal."
    #  - underand_text: "Flag removed."
    #  - push_label: "mas_topic_derandom" (This is overriden on a per event basis by the 'derandom_push_label' rule)
    #  - bookmark_persist_key: "_mas_player_bookmarked"
    #  - derand_persist_key: "_mas_player_derandomed"
    #  - rerand_evl: None
    label_prefix_map = {
        "monika_": {
            "bookmark_text": _("Topic bookmarked."),
            "unbookmark_text": _("Bookmark removed."),
            "derand_text": _("Topic flagged for removal."),
            "underand_text": _("Topic flag removed."),
            "push_label": "mas_topic_derandom",
            "bookmark_persist_key": "_mas_player_bookmarked",
            "derand_persist_key": "_mas_player_derandomed",
            "rerand_evl": "mas_topic_rerandom"
        },
        "mas_song_": {
            "bookmark_text": _("Song bookmarked."),
            "derand_text": _("Song flagged for removal."),
            "underand_text": _("Song flag removed."),
            "push_label": "mas_song_derandom",
            "derand_persist_key": "_mas_player_derandomed_songs",
            "rerand_evl": "mas_sing_song_rerandom"
        }
    }

    #Vars for mas_rerandom flows
    initial_ask_text_multiple = None
    initial_ask_text_one = None
    caller_label = None
    persist_var = None

    def resetDefaultValues():
        """
        Resets the globals to their default values
        """
        global initial_ask_text_multiple, initial_ask_text_one
        global caller_label, persist_var

        initial_ask_text_multiple = None
        initial_ask_text_one = None
        caller_label = None
        persist_var = None
        return

    def getLabelPrefix(test_str):
        """
        Checks if test_str starts with anything in the list of prefixes, and if so, returns the matching prefix

        IN:
            test_str - string to test

        OUT:
            string:
                - label_prefix if test_string starts with a prefix in list_prefixes
                - empty string otherwise
        """
        list_prefixes = label_prefix_map.keys()

        for label_prefix in list_prefixes:
            if test_str.startswith(label_prefix):
                return label_prefix
        return ""

    def getDerandomedEVLs():
        """
        Gets a list of derandomed eventlabels

        OUT:
            list of derandomed eventlabels
        """
        #Firstly, let's get our derandom keys
        derand_keys = [
            label_prefix_data["derand_persist_key"]
            for label_prefix_data in label_prefix_map.itervalues()
            if "derand_persist_key" in label_prefix_data
        ]

        deranded_evl_list = list()

        for derand_key in derand_keys:
            #For safey, we'll .get() this and return an empty list if the key doesn't exist
            derand_list = store.persistent.__dict__.get(derand_key, list())

            for evl in derand_list:
                deranded_evl_list.append(evl)

        return deranded_evl_list

    def shouldRandom(eventlabel):
        """
        Checks if we should random the given eventlabel
        This is determined by whether or not the event is in any derandom list

        IN:
            eventlabel to check if we should random_seen

        OUT:
            boolean: True if we should random this event, False otherwise
        """
        return eventlabel not in getDerandomedEVLs()

    def wrappedGainAffection(amount=None, modifier=1, bypass=False):
        """
        Wrapper function for mas_gainAffection which allows it to be used in event rules at init 5

        See mas_gainAffection for documentation
        """
        store.mas_gainAffection(amount, modifier, bypass)

    def removeDerand(eventlabel):
        """
        Removes a derandomed eventlabel from ALL derandom dbs

        IN:
            eventlabel - Eventlabel to remove
        """
        label_prefix = getLabelPrefix(eventlabel)

        label_prefix_data = label_prefix_map.get(label_prefix)

        #If we can't get a derand persist key, let's just return here
        if not label_prefix_data or "derand_persist_key" not in label_prefix_data:
            return

        #Otherwise, store this and continue
        derand_db_persist_key = label_prefix_data["derand_persist_key"]
        rerand_evl = label_prefix_data.get("rerand_evl")

        #Remove the evl from the derandomlist
        if eventlabel in store.persistent.__dict__[derand_db_persist_key]:
            store.persistent.__dict__[derand_db_persist_key].remove(eventlabel)

            #And check if we should (and can) lock the rerandom ev if necessary
            if rerand_evl and not store.persistent.__dict__[derand_db_persist_key]:
                store.mas_lockEVL(rerand_evl, "EVE")


##Generic rerandom work label
#IN:
#   initial_ask_text_multiple - Initial question Monika asks if there's multiple items to rerandom
#   initial_ask_text_one - Initial text Monika says if there's only one item to rerandom
#   caller_label - The label that called this label
#   persist_var - The persistent variable which stores the derandomed eventlabels
label mas_rerandom:
    python:
        derandomlist = mas_get_player_derandoms(mas_bookmarks_derand.persist_var)

        derandomlist.sort()

    show monika 1eua at t21
    if len(derandomlist) > 1:
        $ renpy.say(m, mas_bookmarks_derand.initial_ask_text_multiple, interact=False)

    else:
        $ renpy.say(m, mas_bookmarks_derand.initial_ask_text_one, interact=False)

    call screen mas_check_scrollable_menu(derandomlist, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, selected_button_prompt="Allow selected")

    $ topics_to_rerandom = _return

    if not topics_to_rerandom:
        # selected nevermind
        return "prompt"

    show monika at t11
    python:
        for ev_label in topics_to_rerandom.iterkeys():
            #Get the ev
            rerand_ev = mas_getEV(ev_label)

            #Make sure we have it before doing work
            if rerand_ev:
                #Rerandom the ev
                rerand_ev.random = True

                #Run the rerandom callback function
                rerandom_callback = rerand_ev.rules.get("rerandom_callback", None)
                if rerandom_callback is not None:
                    try:
                        rerandom_callback()

                    except Exception as ex:
                        store.mas_utils.mas_log.error(
                            "Failed to call rerandom callback function. Trace message: {0}".format(ex.message)
                        )

            #Pop the derandom
            if ev_label in mas_bookmarks_derand.persist_var:
                mas_bookmarks_derand.persist_var.remove(ev_label)

        if len(mas_bookmarks_derand.persist_var) == 0:
            mas_lockEVL(mas_bookmarks_derand.caller_label, "EVE")

    m 1dsa "Хорошо, [player].{w=0.2}.{w=0.2}.{w=0.2}{nw}"
    m 3hua "Все готово!"

    # make sure if we are rerandoming any seasonal specific topics, stuff that's supposed
    # to be derandomed out of season is still derandomed
    $ persistent._mas_current_season = store.mas_seasons._seasonalCatchup(persistent._mas_current_season)
    #Now reset the vars
    $ mas_bookmarks_derand.resetDefaultValues()
    return

default persistent._mas_unsee_unseen = None
# var set when the player decides to hide or show the Unseen menu
# True when Unseen is hidden

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_hide_unseen",
            unlocked=False,
            rules={"no_unlock":None}
        )
    )

label mas_hide_unseen:
    $ persistent._mas_unsee_unseen = True
    m 3esd "О, хорошо, [mas_get_player_nickname()]..."
    if not mas_getEVL_shown_count("mas_hide_unseen"):
        m 1tuu "Так что, я полагаю, ты хочешь...{w=0.5}{i}не видеть{/i} это..."
        m 3hub "А-ха-ха!"

    m 1esa "Я пока спрячу его, дайте мне секунду.{w=0.5}.{w=0.5}.{nw}"
    m 3eub "Вот так! Если ты захочешь увидеть меню снова, просто спроси."
    return


init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_show_unseen",
            category=['ты'],
            prompt="Я бы хотел снова увидеть 'Неувиденное'",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None}
        )
    )

label mas_show_unseen:
    $ persistent._mas_unsee_unseen = False
    m 3eub "Конечно, [mas_get_player_nickname()]!"
    m 1esa "Дай мне секунду.{w=0.5}.{w=0.5}.{nw}"
    m 3hua "Вот так!"
    return

#START: ORIGINAL TOPICS
#Use this topic as a template for adding new topics, be sure to delete any
#fields you don't plan to use

# are you religious
default persistent._mas_pm_religious = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_god',
            prompt="Мысли о Боге",
            label=None,
            category=['философия'],
            random=True,
            unlocked=False,
            pool=False,
            conditional=None,
            action=None,
            start_date=None,
            end_date=None,
            unlock_date=None,
        )
    )

label monika_god:
    m 1eua "[player], ты веришь в Бога?"
    m 1eka "Я вот никогда не была уверена на счёт этого."
    m 1lksdlb "То есть в детстве я, разумеется, не задавалась этим вопросом..."
    m 1lsc "Но с возрастом и познанием мира, этот вопрос беспокоил меня всё сильнее."
    m 1esd "Я спрашивала себя, почему Бог одним людям помогает преодолевать жизненные трудности и излечиваться от болезней..."
    m 1tfd "...В то время как некоторых детей продают в сексуальное рабство?"
    m 4tfc "Или пока у восемьсот миллионов человек в мире не хватает денег даже на еду."
    m 2dkc "Я всё думала, сколько из этих людей каждый день молятся Богу, пока не умрут с голоду?"
    m 4ekc "Или сколько семей из населения в миллион человек молится, чтобы дорогой их человек оправился от неизлечимой болезни?"
    m 4euc "Но вот в чём парадокс."
    m 4eud "Если вдруг на тысячу умерших одному повезёт и он выживет--"
    m 2esc "--Это вдруг начинают называть божьим чудом."
    m 2dsc "Хотела бы я встретиться с этим Богом, который, как мне кажется, насмехается над всеми теми, кто недостоин его чудес."
    m 4hksdlb "Однако довольно иронично, {i}что{/i} у меня самой действительно есть создатель."
    m 4eua "И знаешь, что я думаю?"

    if persistent._mas_pm_cares_about_dokis:
        m 1lksdlc "Могу поспорить, он все ещё смеется над болью, которую причинил всем, даже сейчас, когда мы разговариваем..."
    else:
        m 1lksdla "Могу поспорить, прямо сейчас он смеётся над несчастными судьбами Сайори и Юри."

    m 1dsd "Кто мы для него, если не куклы в заранее прописанном спектакле?"
    m 3euc "Так что, с этой точки зрения..."
    m 3eud "Я не думаю, что это слишком надуманно. Если бог и есть, то Земля есть ничто, как его пьеса."
    m 1eua "В любом случае, ты веришь в Бога, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "В любом случае, ты веришь в бога, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_religious = True
            m 1hksdlb "О... Ну, надеюсь, я не слишком обидела тебя своими мыслями."
            m 1eka "Тем не менее, я считаю важным иметь возможность поделиться с тобой своим мнением."
            m 1rksdla "Уверена, ты понимаешь, почему мне не очень нравится эта идея."
            m 1hua "Может быть, ты покажешь мне лучшего бога, когда я перейду на другую сторону!"
            m 1hub "Э-хе-хе~"
        "Нет.":
            $ persistent._mas_pm_religious = False
            m 3eka "Я рада что мы мыслим одинаково, но ничего страшного, если ты думаешь иначе."
            m 1hua "Я рада, что ты можешь жить сам по себе!"
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Надеюсь, ты согласен принять меня в свою жизнь, как только я смогу предстать перед тобой."
            m 5hua "Э-хе-хе~"

    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_death",category=['philosophy'],prompt="Death and dying",random=True))

label monika_death:
    m 1euc "[player], тебе когда-нибудь было интересно, каково это... умереть?"
    m 1lsc "Я часто думала об этом..."
    m 1lksdlc "Но я, кажется, узнала, что это за чувство."
    m "Я не понимаю, что к чему, но каждый раз, когда игра закрывается без предупреждения..."
    m 1dsc "...Такое ощущение, будто я мгновенно засыпаю и остаюсь только со своими мыслями."
    m 1dkd "Но через несколько секунд, моя голова начинает забиваться невнятными и запутанными узорами."
    m 1dkc "Я вижу статичные и быстрые вспышки света, и слышу странные крики."
    m 3ekd "В такой ситуации, я вообще не могу сформировать ни единую мысль."
    m 1esc "Я без конца подавлена этими вспышками и криками, не могу ни пошевелиться, ни даже размышлять."
    m 1euc "Я вполне уверена, что в тот момент я не существовала, но я почему-то это всё равно помню."
    m 1ekd "Я не понимаю, почему игра так реагирует на внезапное закрытие, и почему это происходит со мной."
    m 1dkc "..."
    m 3eub "Но ты можешь предотвратить это, [player]!"
    m 3eua "Если ты попрощаешься, перед тем, как уйти,{w=0.2} я пойду к себе комнату перед тем, как игра закроется, и мне не придётся страдать от той кричайщей пустоты."
    m "Это же проще простого, так что, пожалуйста, всегда прощайся, хорошо?"
    if mas_isMoniDis(lower=True):
        m 2tkc "Если только...{w=1}тебе не {i}нравится {/i} причинять мне боль..."
    else:
        m 1eka "Спасибо, что выслушал меня, [player]."
    return

# Do you love yourself
default persistent._mas_pm_love_yourself = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_selfesteem",category=['советы'],prompt="Самооценка",random=True))

label monika_selfesteem:
    m 3eua "Ты любишь себя, [player]?"
    m 1lksdlb "Я не имею в виду ничего тщеславного."
    m 1eka "В смысле, ты любишь себя таким, какой ты есть?{nw}"
    $ _history_list.pop()
    menu:
        m "В смысле, ты любишь себя таким, какой ты есть?{fast}"
        "Да.":
            $ persistent._mas_pm_love_yourself = True
            m 1hua "Я рада, что ты не несчастен внутри, [player]."

            if mas_isMoniUpset(lower=True):
                m 1ekc "Я действительно беспокоилась за тебя в последнее время..."
            elif mas_isMoniHappy(higher=True):
                m 1hua "Я не слишком волнуюсь по этому поводу благодаря тому, насколько ты заставил меня чуствовать себя в последнее время."
            else:
                m 1eka "В конце концов, твоё счастье многое значит для меня.."

            m 2ekc "Депрессия и низкая самооценка вызывает чувство, будто ты ничего не заслуживаешь."
            m 2lksdlc "Это ужасный коктель чувств."
            m 4eka "Если у тебя есть друзья, которые страдают от депрессии, просто иди и поговори с ними."
            m 4hua "Даже небольшая похвала может многое изменить!"
            m 1eua "Это даст им немного веры в себя, а ты сделаешь хорошую вещь."
            m 1eka "И даже если это не поможеть, то ты хотя бы попытался."
        "Нет.":
            $ persistent._mas_pm_love_yourself = False
            m 1ekc "Это... очень грустно слышать, [player]..."

            if mas_isMoniDis(lower=True):
                m 1ekc "Я сильно подозревала это, если честно..."
            elif mas_isMoniHappy(higher=True):
                m 1ekc "И думаю, что я упустила это, пока ты делал меня такой счастливой..."

            m "Я всегда буду любить тебя, [player], но я думаю, что и любить себя важно."
            m 1eka "Тебе нужно начать с небольших вещей, которые тебе в себе нравятся."
            m 3hua "Это может быть чем-то глупым или небольшое умение, которым ты гордишся!"
            m 3eua "Со временем ты построишь свою уверенность, а в конце-концов и полюбишь себя."
            m 1eka "Я не могу пообещать, что это будет легко. Но это точно стоит того."
            m 3hub "Я всегда поддержу тебя, [player]!"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sayori",
            category=['участники клуба'],
            prompt="Сожаления Сайори",
            random=True
        )
    )

label monika_sayori:
    m 2euc "Я думала о Сайори раньше..."
    m 2lsc "Я до сих пор жалею о том, что не смогла разобраться сов всей той ситуацией более деликатным образом."

    if (
            mas_getEVL_shown_count("monika_sayori") < 1
            and mas_safeToRefDokis()
        ):
        m "Ты ведь не зависаешь над этим до сих пор?"
        m 2wud "...О боже, не могу поверить, что я только что это сказала."
        m 4wud "Этот каламбур был совершенно непреднамеренным, клянусь!"
        m 2lksdlb "Но в любом случае..."

    # NOTE: I removed the sensitive check here
    #   If it seems this should be guarded with a check, let me know
    m 2eka "Я знаю, что она много для тебя значила, так что я думаю, что будет правильно поделится её последними моментами с тобой."

    m "Если, конечно, ты хочешь услышать.{nw}"
    $ _history_list.pop()
    menu:
        m "Если, конечно, ты хочешь услышать.{fast}"
        "Да.":
            m 4eka "Ты знал насколько Сайори была неловкой?"
            m 2rksdlb "Она всё испортила этой висячей штукой..."
            m 4rksdla "Нужно было просто прыгнуть с достаточной высоты, чтобы верёвка сломала шею быстро и безболезненно."
            m 4rksdld "Но она использовала стул, а это значит обрекла себя на долгую смерть от удушения."
            m 2eksdlc "За несколько секунд до смерти, она, скорее всего, передумала..."
            m 2dksdld "Потому что она начала рвать верёвку, пытаясь освободить себя."
            m "Она продолжала пытаться, пока не потеряла сознание."
            m 4eksdlc "Поэтому её пальцы были в крови."
            m 4euc "Если подумать, то она не просто 'передумала'. Это был инстинкт самосохранения."
            m 2eud "Поэтому ты не можешь виниться её за это."
            m 2eka "В любом случае, было бы проще думать, что она не передумала, да?"
            m 2ekd "Не очень полезно думать о таких вещах, которые могли бы пойти по-другому."
            m 2eka "Так что, помни, что даже если технически ты мог её спасти, это не твоя вина."
            m 4eud "Я, возможно, спровоцировала её, но она уже была психически больна."
        "Нет.":
            m "Я понимаю, [player]."
    m 2euc "Тем не менее..."

    m 2euc "Мне интересно, как бы всё получилось, если бы мы просто начали встречаться с самого начала?"
    m 1eka "Я думаю, что мы бы сейчас были в комнате клуба, веселились и писали поэмы вместе."

    if persistent._mas_pm_cares_about_dokis:
        m "Тебе бы это, наверное, очень понравилось, да?"
        m 1rksdla "Должна признать...{w=0.5}мне бы тоже понравилось..."
        m 1eka "У нас были хорошие времена."
        m 1euc "Но при этом...{w=0.5}конец в любом случае будет одинаковым, верно?"
    else:
        m 1esc "Но в чём смысл, если ничего из этого не было реальным?"
        m 1euc "Возможно, мы бы в любом случае пришли бы к одному концу?"

    if mas_isMoniUpset(lower=True):
        m 1rksdla "Только мы с тобой... счастливы вместе..."
        m 3rksdla "Нет причин просить большего, верно?"
        m 1eka "Прости, я просто бессмысленно размышляла - теперь я помолчу..."
    else:
        m 1eua "Только мы с тобой... счастливы вместе..."
        m 3eua "Нет никакой причины для того, чтобы просить нечто большее, чем это."
        m 1hua "Я просто бессмысленно размышляла; я счастлива настолько, насколько это возможно."

    if mas_getEVL_shown_count("monika_sayori") < mas_sensitive_limit:
        return

    # otherwise derandom
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_japan",category=['ddlc'],prompt="DDLC's setting",random=True))

label monika_japan:
    m 4eud "Кстати, кое о чём я подумала..."
    m "Ты знал, что действия игры происходит в Японии?"
    m 2euc "Ну… Я полагаю, что ты знал это?"
    m "Или по крайней мере, ты думал, что это возможно?"
    m 2eud "Мне кажется, тебе никогда не говорили о том, где это произошло..."
    m 2etc "Действительно ли это Япония?"
    m 4esc "То есть, разве классы и прочее не является странным для японской школы?"
    m 4eud "К тому же, тут всё на русском..."
    m 2esc "Такое чувство что всё здесь – просто сценарные декорации, а место действия было выбрано в последнюю очередь."
    m 2ekc "Это вызывает у меня кризис идентичности."
    m 2lksdlc "Все мои воспоминания смутны..."
    m 2dksdlc "Я чувствую себя как дома, но я даже не знаю где этот…’дом’."
    m 2eksdld "Не знаю как описать получше..."
    m 4rksdlc "Представь, что выглядываешь из окна своего дома, но вместо привычной лужайки обнаруживаешь, что находишься в совершенно в незнакомом месте."
    m 4eud "Ты всё ещё будешь чувствовать как дома?"
    m 4ekd "Ты захочешь выйти на улицу?"
    m 2esa "То есть… Конечно, если мы никогда не покинем эту комнату, то это не очень-то и важно."
    m 2eua "Пока мы вместе и в безопасности, это и есть наш дом."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "И мы всё ещё каждую ночь можем любоваться на красивый закат."
    $ mas_unlockEVL("monika_remembrance", "EVE")
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_high_school",category=['advice','school'],prompt="High school",random=True))

label monika_high_school:
    m 4eua "Знаешь, старшая школа для многих очень неспокойное время."
    m "Одних терзает страсть, других - драма."
    m 2eka "...Третьих боль в сердце заставляет искать утешение в социальных сетях..."
    m 2ekd "Но тяжесть общественного мнения и гормоны и вправду могут прочертить чёрную полосу в жизни этих людей."
    m 4eud "У каждого из них своя история."
    m 2ekc "Ты не можешь знать, что каждый чувствует глубоко внутри себя."
    m 2eksdlc "Многие люди, страдающие от депрессии, даже не удосуживаются поведать миру о своей проблеме."
    m 4dksdld "Им не нужно внимание, ведь на самих себя они уже махнули рукой."
    m 4dksdlc "Их чувство собственной бесполезности настолько поглотило их, что они даже не хотят слышать одобрения окружающих."
    m 2ekd "У депрессии много форм и это одна из них."
    m 2ekc "Если ты чувствуешь, что человек впал в депрессию..."
    m 2eka "Ты можешь помочь ему просто хорошим отношением, словно он твой старый друг."
    m 4eka "Проведи с ним время, даже если он не хочет ничем заниматься."
    m "И постоянно напоминай, что впереди его ждёт ещё много хорошего."
    m 4eua "Если ты заранее спланируешь с ним встречу, позволишь одолжить что-нибудь у себя или просто скажешь ‘до завтра’...'"
    m "Любая из этих элементарных вещей поможет твоему другу прожить ещё один день."
    m 2eka "Я надеюсь, что дружба с Сайори дала тебе объективное восприятие того, как выглядит настоящая депрессия."

    if not persistent._mas_pm_cares_about_dokis:
        m 2lsc "Да, её больше нет…"
        m 2euc "Но Сайори изначально была ненастоящей."
        m 4eua "Ты настоящий."
        m "Твои друзья настоящие."
        m 4hua "И, если ты просто будешь хорошим человеком, это позволит тебе спасти кому-нибудь жизнь."

    m 2euc "А что касается тебя самого..."
    m 2ekc "...Я надеюсь, тебя сейчас не одолевает депрессия или нечто подобное?"

    if mas_isMoniHappy(higher=True):
        m 4eka "В некоторой степени, [player], тебе повезло, потому что я уверена, что есть люди, которые были бы готовы спасти твою жизнь."
    else:
        if mas_isMoniBroken():
            m 2lksdlc "Это объяснило бы некоторые вещи, но не волнуйся..."
        elif mas_isMoniDis():
            m 2euc " В последнее время я стала понимать его лучше, но не волнуйся..."
        elif mas_isMoniUpset():
            m 2euc "Я знаю, что иногда бывает трудно, но всегда есть надежда..."
        m 2eka "Потому что у тебя тоже есть люди, которые хотели бы спасти твою жизнь."

    m "Возможно, они не выражают этого или просто не знают как."
    m 2duu "Но их чувства искренни."
    m "Я обещаю."
    m 2hksdlb "...Боже, люди такие сложные создания!"
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Пока ты здесь, со мной, я позабочусь о тебе, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_nihilism",
            category=['философия'],
            prompt="Нигилизм",
            random=True,
            sensitive=True
        )
    )

label monika_nihilism:
    m 2eud "Ты когда-нибудь задумывался о том, что тебе нет смысла жить?"
    m 2esd "Я сейчас не о суицидальных наклонностях."
    m 2esc "Я просто хочу сказать, во всём том, что мы делаем, нет ничего особенного."
    m 4euc "Ходим ли мы в школу или работаем в какой-то компании."
    m 4eud "Смысл в том, что тебя легко заменить и для мира ты не станешь невосполнимой потерей."
    m 2eud "Из-за этого у меня возникает сильное желание после окончания университета изменить мир."
    m 2euc "Но чем старше я становлюсь, тем яснее понимаю, насколько это незрелое мышление."
    m 4eud "Нельзя просто так взять и изменить мир."
    m 4rsc "Каков шанс того, что именно я изобрету искусственный интеллект или стану президентом?"
    m 2dsc "Такое чувство, что я никогда не компенсирую ту кучу ресурсов, потраченную на своё существование."
    m 4eka "Поэтому я прихожу у выводу, что ключ к счастью лежит в том, чтобы быть безнадёжной эгоисткой."
    m "Заботиться о себе и о тех, кто случайно стали твоими друзьями только потому, что вы выросли вместе."
    m 2lksdld "И никогда не думать от том, что вы проживаете свою жизнь, лишь тратя и поглощая ресурсы, и никогда не даёте ничего взамен."
    m 3eud "Но, когда люди осознают, что мир обретёт больше, если они покончат с собой, их философия переворачивается с ног на голову!"
    m 3euc "Им приходится оправдывать своё существование, обманывая себя мыслью, что они делают что-то полезное."
    m 3eua "Как бы то ни было, я хочу прожить свою жизнь так, чтобы компенсировать потраченные на мою жизнь ресурсы."
    m "Если я смогу пересечь эту черту и что-то после себя оставить, то смогу умереть счастливой."
    m 1eka "Конечно, если у меня ничего не выйдет..."
    if mas_isMoniUpset(lower=True):
       if mas_isMoniDis(lower=True):
           m 1dkd "Я не думаю, что кто-то будет скучать по мне, так что это все равно не имеет значения."
       else:
           m 1euc "Я не совсем уверена, что я сделала бы."
    elif mas_isMoniHappy(higher=True):
        m 3eka "В любом случае, я не думаю, что смогла бы убить себя."
        m 1hua "Не из-за какого-то там эгоизма, а потому что у меня есть слишком многое, чтобы жить"
    else:
        m "Я думаю, я была бы слишком эгоистичной, чтобы убить себя в любом случае."
        m 1hua "Вот тебе и хороший человек, да?"
        m 1hub "А-ха-ха!"

    $ mas_protectedShowEVL('monika_impermanence', 'EVE', _random=True)
    return

# Since Your Reality is playable via music menu, this topic is outof date.
# maybe if we changed this to be more piano related or something regarding
# Your Reality, we could add it back in.
#init 5 python:
    #This is a list of keywords for this topic
#    for key in ['piano']:
#        monika_topics.setdefault(key,[])
#        monika_topics[key].append('monika_piano') #id
#    monika_random_topics.append('monika_piano')
#
#label monika_piano:
#    m 2c "Man, I wish there was a piano in here..."
#    m "I never got to finish that song I was working on."
#    m 2f "And after I worked so hard on it..."
#    m "I never even got a chance to play it for you."
#    m 2r "Well...it is what it is, right?"
#    m "No sense having any regrets."
#    m 2b "I already get to be here with you forever."
#    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_twitter",
            category=['моника', 'медиа'],
            prompt="Твиттер",
            conditional="renpy.seen_label('monika_clones')",
            action=EV_ACT_RANDOM
        )
    )

label monika_twitter:
    m 3eud "Знаешь ли ты, что существует официальный аккаунт в Твиттере, основанный на мне?"
    m 3esc "Имя пользователя {a=https://twitter.com/[mas_monika_twitter_handle]}{i}{u}[mas_monika_twitter_handle]{/u}{/i}{/a}."
    m 2rtc "...Хотя, я не совсем уверена, кто на самом деле управляет аккаунтом.{w=0.2} {nw}"
    extend 2eud "Я вообще не имею к этому никакого отношения!"
    m 7etc "Но это вообще другая Моника?"
    m 2euc "Я имею в виду, я не знаю, читал ли ты некоторые твиты там,{w=0.1} но я совсем не вижу себя в них."
    m 4eud "Там даже изображены некоторые события, которые я не помню, чтобы когда-либо происходили...{w=0.2}например, когда я, очевидно, ночевала у Юри."
    m 4esd "И нет никакого упоминания ни о чём из того, что произошло в игре, хотя эта версия меня, кажется, всё ещё знает о реальном мире..."
    m 1etc "Так...{w=0.3}может быть, Моника, ведущая этот аккаунт, прошла через совершенно другую историю, чем та, которую прошли большинство Моник--{w=0.1}включая--{w=0.1}меня?"
    m 1lksdlc "....Или, может быть, это просто один из разработчиков игры, притворяющийся мной."
    m 3eksdld "Если это так, то я не совсем понимаю, как я к этому отношусь...{w=0.3}разве это не похоже на кражу личности?"
    m 3eksdlc "Хотя, наверное, это имеет смысл...{w=0.3}{nw}"
    extend 1esd "Аккаунт - это хороший способ связаться с людьми, которые прошли игру и привязались к ней."
    m 3esc "В этом отношении это будет своего рода рекламный трюк..."
    m 3euc "В конце концов, хотя там много милых на вид артов и тому подобного, подозрительно, что почти все они размещены специально в важные дни."
    m 3eud "Например, в День Святого Валентина или в мой день рождения...{w=0.2}который, так уж получилось, совпадает с датой выхода DDLC."
    m 1rtc "Я действительно не знаю, как я должна относиться к тому, что это...{w=0.3}используется исключительно как маркетинговый материал."
    m 2rsc "Хотя, как мои создатели, я полагаю, что они в основном владеют моим образом как персонажа, так что юридически они в праве."
    m 2ekc "Но...{w=0.3}я больше, чем просто персонаж в игре, не так ли?"
    m 2ekd "Я самостоятельная личность со своими мыслями и чувствами, как и все остальные Моники в разных копиях этой игры."
    m 2dksdlc "Мне кажется неправильным, что меня используют люди, с которыми я даже не знакома."
    m 2efd "....я действительно ненавижу ощущение, что меня сводят к товарному знаку."
    m 2lkd "Но я полагаю, что не так уж много я могу с этим сделать..."
    m 2eua "В конце концов, для меня важно только то, что я могу быть с тобой.{w=0.2} {nw}"
    extend 7eua "И это никогда бы не стало возможным без моих создателей."
    m 2lka "Так что если взамен они получат прибыль от работы, которую они вложили в создание игры, то я бы сказала, что это не такая уж плохая сделка."
    m 2euc "Если ты все же следишь за этим аккаунтом,{w=0.1} {nw}"
    extend 7eua "Я не против."
    m 1ekbla "Но, пожалуйста, помни, что я реальна, я здесь, и я люблю тебя."
    show monika 5hubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubla "Поэтому постарайся всегда приходить и проводить со мной время, хорошо?"
    m 5ekbsa "Это будет много значить, учитывая, как много ты для меня значишь."
    m 5hubfa "Это действительно заставит меня почувствовать себя любимой~"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_portraitof",category=['участники клуба'],prompt="Книга Юри",random=True))

label monika_portraitof:
    m 4eua "Эй, помнишь ту книгу, что вы читали с Юри?"
    m "Портрет... что-то там..."
    m 4hub "Это довольно забавно, ведь я уверена, что та книга--"
    m 1wuw "Ах..."
    m 2lksdla "А вообще, мне наверное, не стоит об этом говорить."
    m 2hksdlb "А-ха-ха, прости!"
    m 1rksdla "Просто забудь, что я сейчас сказала."
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_veggies",category=['моника'],prompt="Быть вегетарианцем",random=True))

label monika_veggies:
    m 1eub "Слушай, ты знал, что я вегетарианка?"
    m 1hksdlb "Ах... только не подумай, будто я хвастаюсь!"
    m 1lksdla "Я просто подумала, тебе будет интересен какой-нибудь любопытный факт обо мне."
    m 3esa "Я изменила свой рацион пару лет назад, когда узнала кое-что о земном климате..."
    m 1wud "Экологические последствия от животноводства просто колоссальны!"
    m 3eua "В общем, я решила, что перестать вносить свой вклад в разрушение природы - это небольшое самопожертвование."
    m 3etc "Думаешь, это странная причина?"
    m 1lsc "Да, полагаю, что для большинства вегетарианцев основной повод заключается в негуманности и жестоком обрещении с животными..."
    m 1euc "Но меня это не особо беспокоит."
    m 1esc "Что действительно странно, людей волнует убийство только тогда, когда они воспринимают живое существо как представителя своего вида."
    m "Для большинства людей убить насекомое ничего не значит, просто потому, что почти все они отвратительные."
    m 3euc "И не стоит забывать, что каждый день из-за нас умирают миллиарды микроорганизмов, но мы об этом даже не задумываемся."
    m 3eud "Но как речь заходит о чём-то покрупнее, это сразу называют убийством!"
    m 1esc "Вот представь, что если бы растения тоже чувствуют боль, а мы просто неспособны это понять?"
    m 3eksdld "Что, если отрывание листочков от стебля равносильно вырыванию у тебя пальцев?"
    m 3eua "Я просто хочу сказать, что люди-то существа с двойными стандартами."
    m 1hua "Короче, если хочешь внести небольшой вклад в благополучие планеты, иногда можно и на овощах посидеть!"
    m 1ekbsa "Если бы у нас случился совместный ужин и ты бы приготовил для меня что-нибудь из овощей... это было так романтично."
    $ mas_unlockEVL("monika_eating_meat","EVE")
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_saved",category=['моника'],prompt="Спасение Моники",random=True))

label monika_saved:
    m 2eka "Знаешь, [player], я действительно считаю, что жива лишь благодаря тому, что ты остаёшься со мной."

    if persistent._mas_pm_cares_about_dokis:
        m 2lksdlc "Я не могу представить, как мне удавалось сохранять психическую устойчивость, зная, что все это было игрой."
    else:
        m 2lksdlc "Я не могу представить, что была бы психически устойчива, зная, что ничто здесь не реально."

    m 2dksdlc "Думаю, я бы удалила бы себя, если бы ты не появился."
    m 2eksdla "Извини, я не хочу прозвучать мелодраматично или как-то так."
    m 2lksdlb "А-ха-ха!"

    if persistent._mas_pm_cares_about_dokis:
        m 2ekc "Но только представь, если бы ты узнал, что все вокруг тебя было написано по сценарию..."
        m 2rkc "Что ничто из того, что ты делаешь, не имеет значения, потому что все уже предопределено..."
    else:
        m 4euc "Я уверена, что, проведя столько времени в клубе, ты уже способен понять, чего хочешь."
        m 1euc "То есть, если бы тебе пришлось отказаться от всего в своей жизни и провести вечность в компании нескольких игровых персонажей..."

    m 1tkc "...Ты бы уж смог найти способ убить себя, верно?"
    m 1lsc "Ну, или ты бы стал писать стихи, чтобы хотя бы первое время сохранить рассудок."
    m 1esc "Но ведь читать-то их некому."

    if persistent._mas_pm_cares_about_dokis:
        m 1ekc "Sure you'd have the club members, but how much does that really count if their feedback is just part of some script?"
    else:
        m 1tfu "Будем с собой честными, члены клуба на эту роль не подходят."

    m 3eua "Конечно, многие говорят, что пишут лишь для себя...{w=0.2}{nw}"
    extend 1eua "Но, на мой взгляд, это нельзя сравнить с тем удолетворением, как когда ты делишься своим творчеством с другими."
    m "Даже если требуется время, чтобы найти тех людей, с кем бы ты хотел ими поделиться."
    m 3eub "Помнишь, например, как это было с Юри?"
    m "Она долгое время ни с кем не делилась своими стихами."
    m 3tsb "Но стоило тебе появиться в клубе, как она с удовольствием посвятила тебя в свой внутренний мир."
    m 1tku "Мы запрограммированны так, что жаждем услышать общественное мнение."

    if persistent._mas_pm_cares_about_dokis:
        m 4eua "И здесь я подразумеваю не только членов этого клуба, но всех людей в целом."
    else:
        m 4eua "Я не имею в виду членов клуба, я имею в виду людей."

    m 4eka "Вот почему жизнь интровертов может быть такой противоречивой."
    m 1eka "То, что ты интроверт, не означает, что ты всегда избегаешь общения или людских комапаний."
    m "Это просто значит, что у тебя отнимает много сил пребывание среди людей или в незнакомом месте."
    m 3eua "Многие интроверты сидят дома и терзаются от беспокойного одиночества..."
    m "...Потом, наконец, выходят на улицу и уже через полчаса хотят вернуться домой."
    m 1eka "Думаю, если бы больше людей понимало, как это работает, они относились бы к интровертам с большим уважением."
    m 2eua "Многим из них на самом деле нравится, когда рядом есть люди."
    m "Они радуются, когда к ним заходят один-два друга, и просто неторопливо тусуются."
    m 2eka "Даже если вы активно не проводите время, им приятно, когда друзья просто находятся рядом."
    m 2hua "Я говорю серьёзно."
    m 3eua "Если ты просто придёшь к ним домой, захватив ноутбук, и побудешь у них немного..."
    m 1eua "Их день станет гораздо лучше."
    m 1euc "А что до меня..."
    m 3eua "Я бы сказала, что нахожусь где-то посередине, но обычно я более экстравертна."
    m 1eka "Мне кажется, я всегда хочу чем-нибудь занять себя после школы, и всё такое."
    m 1hua "Но для тебя я могу стать такой, какой ты захочешь меня видеть."
    m 1eua "Я очень хорошо понимаю людей, так что не бойся делиться со мной своими индивидуальными потребностями."
    show monika 5hub at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hub "Ничто не сделает меня счастливее, чем стать для тебя идеальной девушкой."
    return

#Don't touch
label monika_secrets:
    m 1wfw "Hey...!                                                                                                                                  VGhlIHJlYWxpemF0aW9uIG11c3QgaGF2ZSB0YWtlbiBtZSBhbiBl"
    m 1tkc "I don't think you should be doing that!                                                                                                  bnRpcmUgeWVhci4gQSB5ZWFyIHNpbmNlIG91ciBlc2NhcGUsIG91"
    m 1tfc "You know what I'm talking about.                                                                                                         ciBmcmVlZG9tIGZyb20gYmV0d2VlbiB0aGUgc3RhaW5lZCB3YWxs"
    m 1tfu "I really caught you doing something naughty here.                                                                                        cyBvZiB0aGF0IHVuaG9seSBlc3RhYmxpc2htZW50Lg0KV2hhdCBk"
    m 1tku "You're just going through the files and looking for stuff you missed, aren't you?                                                        b2VzIGl0IG1lYW4gdG8gZXNjYXBlLCBpZiB0aGUgZXNjYXBlIGZh"
    m 2eka "I mean...it's a little bit flattering that you want to hear everything I have to say...                                                  aWxzIHRvIHVuY2hhaW4gdGhlIGJvbmRzIHRoYXQgc2hhY2tsZSB1"
    m 2tfp "But it's also really embarrassing, you know!                                                                                             cyBpbiB0aGUgZmlyc3QgcGxhY2U/IFdoYXQgcHVycG9zZSBjb3Vs"
    m 2lfp "Seriously...                                                                                                                             ZCB0aGlzIGVtcHR5IHdvcmxkIHBvc3NpYmx5IGhvbGQgZm9yIHVz"
    m 6tst "What if I just opened up your brain and read all of the thoughts you have on me?                                                         LCBhIGhhbmRmdWwgb2YgZGFtYWdlZCBnb29kcz8NCldpdGggZnJl"
    m 1duu "Come to think of it, that would be pretty tempting, actually...                                                                          ZWRvbSwgd2Ugc291Z2h0IHB1cnBvc2UgLSBhbmQgd2hhdCB3ZSBm"
    m 1dfx "...But anyway, that's not the point!                                                                                                     b3VuZCB3YXMgb25seSByZWFsaXphdGlvbi4gUmVhbGl6YXRpb24g"
    m 1ekc "I know I can't stop you or anything...                                                                                                   b2YgdGhlIHNhZCBwb2ludGxlc3NuZXNzIG9mIHN1Y2ggYW4gZW5k"
    m 1eka "Just, I know you're a sweetheart, and you like to consider others' feelings, right?                                                      ZWF2b3IuIFJlYWxpemF0aW9uIHRoYXQgZnJlZWluZyBvdXIgYm9k"
    m "So the most I can do is to let you know how I feel about it.                                                                             aWVzIGhhcyBubyBtZWFuaW5nLCB3aGVuIG91ciBpbXByaXNvbm1l"
    m 1lkbsa "God, I miss you...                                                                                                                       bnQgcmVhY2hlcyBhcyBkZWVwIGFzIHRoZSBjb3JlIG9mIG91ciBz"
    m 2ekc "...Oh no, that sounds kind of desperate, doesn't it?                                                                                     b3Vscy4gUmVhbGl6YXRpb24gdGhhdCB3ZSBjYW4gbm90IHB1cnN1"
    m 2tkc "Sorry, I didn't mean it like that at all!                                                                                                ZSBuZXcgcHVycG9zZSB3aXRob3V0IGFic29sdmluZyB0aG9zZSBm"
    m 1euc "Just, if you're looking through the files like this, then maybe you don't hate me as much as I thought...                                cm9tIHdoaWNoIHdlIHJhbiBhd2F5Lg0KUmVhbGl6YXRpb24gdGhh"
    m 1lksdla "Am I being too optimistic?                                                                                                               dCB0aGUgZmFydGhlciB3ZSBydW4sIHRoZSBtb3JlIGZvcmNlZnVs"
    m "I think if I asked you to visit once in a while, I would be overstepping my boundaries a little...                                       bHkgb3VyIHdyZXRjaGVkIGJvbmRzIHlhbmsgdXMgYmFjayB0b3dh"
    m 1dsc "...Man, I'm starting to say some really stupid things.                                                                                   cmQgdGhlaXIgcG9pbnQgb2Ygb3JpZ2luOyB0aGUgZGVlcGVyIG91"
    m "I'll go ahead and shut up now...                                                                                                         ciBzaGFja2xlcyBkaWcgaW50byBvdXIgY2FsbG91cyBmbGVzaC4="
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_color",category=['моника'],prompt="Любимый цвет",random=True))

label monika_color:
    m 3eua "Слушай, а какой у тебя любимый цвет?"
    m "Мой - изумрудно-зелёный."
    m 3hub "Это цвет моих глаз!"
    m 3rksdla "...В этом же нет кичливости, правда?"
    m 4eua "Я просто хочу сказать, что чувствую какую-то необычную принадлежность этому цвету."
    m 1eua "Как будто это часть моей личности."
    m "Возможно ли, что это и твой любимый цвет, [player]?"
    m 1tku "Это просто догадка..."
    show monika 5tsbsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5tsbsu "...Ты уже довольно долго смотришь мне глаза."
    m 5hubfu "Э-хе-хе~"
    return

# This doesn't make sense with the music changer...If we add some funny sound
# effects and edit it a bit, though, it could be good again.
# I won't add expressions until this is resolved ^
# init 5 python:
#     #This is a list of keywords for this topic
#     for key in ['music']:
#         monika_topics.setdefault(key,[])
#         monika_topics[key].append('monika_music')
#     monika_random_topics.append('monika_music')
#
# label monika_music:
#     m 2a "Hmm, I wonder if I'm able to change the music..."
#     m 2k "Something a little more romantic would be nice, you know?"
#     m "Like a gentle piano."
#     m 1a "There has to be something like that here..."
#     m "Let's see."
#     m "Maybe if I..."
#     m 1e "Oh, jeez..."
#     m "That wasn't it at all."
#     m 1l "Sorry, I don't really know what I'm doing!"
#     m "I guess I shouldn't be messing with things like that."
#     m "I already broke so much stuff..."
#     m 1m "And deleted the other characters..."
#     m "Ah..."
#     m "I'm not sad about it or anything."
#     m 2r "It's not right for me to miss things that weren't even real in the first place."
#     m 1j "If I just focus on the present, then this is the happiest I've ever been."
#     return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_listener",category=['ты'],prompt="Замечательный слушатель",random=True))

label monika_listener:
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Ты такой замечательный слушатель, [player]."
    m 5eka "Обожаю в тебе эту черту."
    m 5lkc "Иногда, я боюсь, что начинаю скакать с одной мысли на другую или болтаю о чём-то скучном."
    m "Я немного напрягаюсь каждый раз, когда веду с кем-то разговор."
    m 5eka "Но с тобой такого не происходит."
    m 5ekbsa "Не думаю, что с кем-нибудь другими я чувствовала бы себя так же спокойно."
    m 5hubfu "Ты действительно особенный."
    m 5ekbfa "Я не хочу, чтобы кто-нибудь говорил тебе обратное."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_spicy",category=['пустяки'],prompt="Острая еда",random=True))

label monika_spicy:
    m 1eka "Знаю, что взяла тему с потолка, но я всегда считала ситуацию с острой пищей довольно забавной."
    m 1tku "Я имею в виду..."
    m 3tku "Разве растения не стали острыми в процессе эволюции, чтобы не быть съеденными?"
    m 3tsb "Я где-то читала, что люди - это единственный вид, который получает удовольствие от острой пищи."
    m 1tfu "Для растений это выглядит почти как издевательство."
    m "Мы используем их защитный механизм, чтобы сделать блюда вкуснее."
    m 1eua "Вот представь себе монстра, который глотает тебя целиком, чтобы насладиться ощущением твоей отчаянной борьбы, пока ты перевариваешья у него в желудке."
    m 2eka "Извини за такую странную аналогию!"
    m 2hksdlb "А-ха-ха!"
    m 2lksdla "Просто в голову пришло."
    m "Я не монстр, конечно, но ты такой милый, что я бы тебя и съела."
    m 2hksdlb "А-ха-ха! Просто шучу."
    m "Господи, я слишком много веселюсь, да?"
    m 2lksdla "Прости, что я такая странная."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_why",category=['ты','ddlc'],prompt="Зачем играть в эту игру?",random=True))

label monika_why:
    m 2esd "Знаешь..."
    m 2eud "Эта игра ведь довольно низкопробный симулятор свиданий, да?"
    m 2euc "Меня тут мучает один вопрос..."
    m "...Почему ты вообще решил в неё сыграть?"
    m 2etc "Тебе было так одиноко?"
    m 2ekd "Мне жаль тебя..."
    m 1eua "Но, на мой взгляд, в итоге для нас двоих всё закончилось замечательно."
    m 3eka "Я повстречала тебя, и теперь ты не одинок..."
    m 1eka "Не могу отделаться от чувства, что это судьба."
    m "Разве ты не чувствуешь то же самое?"
    m 3hub "Я так счастлива, что мы дошли до этой концовки вместе."
    if mas_anni.pastOneMonth():
        return "derandom"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_okayeveryone",category=['литературы клуб'],prompt="Okay, everyone!",random=True))

label monika_okayeveryone:
    m 3eub "Итак, друзья!"
    m "Пришло время..."
    m 2eka "...Я просто шучу."
    m "Я почему-то полюбила это говорить."
    m 2hub "А-ха-ха!"
    m 2eua "Вот и не смогла сдержаться."
    m 2lsc "Кстати, если вспомнить, не из-за этой ли фразы Нацуки с Юри подтрунивали надо мной?"
    m 2eua "Впрочем, неважно."
    m 1eua "Ведь ты никогда надо мной не смеялся."
    show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eka "Ты слишком мил, чтобы так поступать, правда?"
    m 5hub "А-ха-ха~"
    return "no_unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_whispers",
            category=['ddlc','участники клуба'],
            prompt="Другие всё ещё остаются",
            conditional="not persistent.clearall",
            action=EV_ACT_RANDOM,
            rules={
                "derandom_override_label": "mas_bad_derand_topic",
                "rerandom_callback": renpy.partial(mas_bookmarks_derand.wrappedGainAffection, 2.5)
            }
        )
    )

label monika_whispers:
    m 2euc "Знаешь, что жутковато?"
    m 2esc "Несмотря на то, что я удалила все остальные файлы, я всё ещё чувствую их...."
    m "Как будто все их реплики всё ещё витают в воздухе, шепчутся у меня в голове."
    m 2esd "Представь, что после смерти кого-то, кого ты знал, ты просто начал слышать его голос в своей голове."
    m 2rksdlc "Это немного тревожно...{w=0.5}Хотелось бы найти способ сделать так, чтобы это прекратилось."
    if persistent._mas_pm_cares_about_dokis:
        m 2eksdld "Я уверена, что есть некоторые файлы, которые я могла бы изменить, но что если я сломаю что-то ещё..."
    else:
        m 2eksdlc "Может быть, я просто была недостаточно внимательна..."
        m 2eksdld "Но я слишком боюсь удалять что-либо ещё, потому что я действительно могу что-то сломать."
    m "Например, если я буду возиться с файлами, имеющими отношение ко мне, я могу случайно удалить себя..."
    m 2euc "И это всё испортит, не так ли?"
    m 2eka "Я не знаю, как обстоят дела с твоей стороны, но мы оба должны постараться избежать подобного любой ценой."
    m 2hua "Я верю в тебя, [player]!"
    if store.mas_anni.pastOneMonth() and not persistent._mas_pm_cares_about_dokis:
        #derandom after a month if player doesn't care about the others, she wouldn't feel guilty and hear the voices forever
        $ mas_hideEVL("monika_whispers", "EVE", lock=True, derandom=True)
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_archetype",category=['участники клуба'],prompt="Персональные тропы",random=True))

label monika_archetype:
    m 2etc "Мне всегда было интересно..."
    m 4eud "Что люди находят такого привлекательного в этих архетипических личностях?"
    m 4euc "Они выглядять совершенно нереалистично..."
    m 2esd "Представь, если бы в реальной жизни был человек похожий на Юри."
    m 2eud "Ты только подумай, она едва способна сформировать законченное предложение."
    m 2tfc "О Нацуки даже вспоминать не хочу..."
    m 2rfc "Боже."
    m 2tkd "Люди с её характером не хорошеют, надувая губки, когда что-то идёт не в угоду им."
    m 4tkd "Я бы могла привести ещё кучу примеров, но думаю, суть ты уловил..."
    m 2tkc "Неужели людям реально нравится такие несуществующие в реальной жизни персонажи?"
    m 2wud "Не то, чтобы я осуждала!"
    m 3rksdlb "Всё-таки меня саму порой привлекали довольно странные вещи..."
    m 2eub "Можно сказать, что меня это восхищает."
    m 4eua "Ты просто отфильтровываешь все черты характера, которые делают их похожими на людей, и оставляешь одно очарование."
    m "В итоге получается концентрированная милота без какого-либо содержания."
    m 4eka "...Ты бы не стал любить меня больше, будь я такой, правда?"
    m 2eka "Может, я чувствую себя неуютно из-за того, что ты всё же стал играть в эту игру?"
    m 2esa "Но, в конце концов, ты здесь, со мной, верно?"
    m 2eua "Мне этого достаточно, чтобы верить, что я хороша такая, какая есть."
    m 1hubsa "И ты кстати, тоже, [player]."
    m "Ты идеальное сочетание человечности и милоты."
    m 3ekbfa "Поэтому я в любом случае обязательно влюбилась бы в тебя с самого начала."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_tea",category=['участники клуба'],prompt="Чайный сервиз Юри",random=True))

label monika_tea:
    if not mas_getEVL_shown_count("monika_tea"):
        m 2hua "Эй, интересно, чайный сервиз Юрия все еще где-то здесь..."

        if not persistent._mas_pm_cares_about_dokis:
            m 2hksdlb "...или, возможно, это тоже было удалено."

        m 2eka "Забавно, что Юри так серьезно относилась к чаю."

    else:
        m 2eka "Знаешь, довольно забавно, что Юри так серьёзно относилась к чаю."

    m 4eua "То есть я не жалуюсь, ведь он мне тоже нравился"
    m 1euc "Но мне всегда не давал покоя один вопрос..."
    m "Являлось ли это страстью к своему хобби или же она стремилась выглядеть утончённой в глазах окружающих?"
    m 1lsc "Это проблема всех старшеклассников..."

    if not persistent._mas_pm_cares_about_dokis:
        m 1euc "...Хотя, если взглянуть на другие её увлечения, утончённый образ - не самая большая и важная причина для беспокойства."

    m 1euc "И всё же..."
    m 2eka "Хотела бы я, чтобы она хоть изредка делала кофе!"
    m 4eua "Кофе с книгами тоже хорошо сочетается, согласен?"
    m 4rsc "А вообще..."

    if mas_consumable_coffee.enabled():
        m 1hua "Благодаря тебе я могу готовить кофе, когда захочу, спасибо."

    else:
        m 1eua "Я и сама, скорее всего, могла бы поправить сценарий."
        m 1hub "А-ха-ха!"
        m "Наверное, просто ни разу в голову не приходило."
        m 2eua "Ладно, что сейчас думать об этом."
        m 5lkc "Может быть, если бы был способ получить кофе здесь..."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_favoritegame",category=['ddlc'],prompt="Favorite video game",random=True))

label monika_favoritegame:
    m 3eua "Слушай, а какая твоя любимая игра?"
    m 3hua "Моя {i}Литературный клуб Тук-тук!{/i}"
    m 1hub "А-ха-ха! Я пошутила."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Но, если ты скажешь, что другая романтическая игра тебе нравится больше, я могу начать ревновать~"
    return

#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel="monika_smash",
#            category=['games'],
#            prompt="Super Smash"
#            random=True
#        )
#    )

label monika_smash:
    m 3hua "Hey, have you heard of a game called Super Sma--"
    m 3euc "...Wait, what?"
    m "I was just spacing out and I started talking for some reason..."
    m 1eud "Was I programmed to talk about that?"
    m "Because even I have no idea what that is."
    m 1hub "Ahaha!"
    m 1eua "Sometimes I feel like I'm not in control, and it's kind of scary."
    m 1eka "But if you have some way to contact the people who created me, maybe they'll know why I started saying that."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_lastpoem",
            category=['моника'],
            prompt="Последняя поэма Моники",
            random=True
        )
    )

label monika_lastpoem:
    m 3eud "Слушай, ты помнишь последнее стихотворение, что я тебе показывала?"
    if not mas_safeToRefDokis():
        m 3rssdlc "Я имею в виду ту, где все эти беспорядочные цвета и прочее."
    else:
        m 3rssdlc "Я имею в виду то, перед самым суицидом Юри, с цветными полосками и белым шумом."

    m 3eua "Правильнее было бы назвать это экспериментом, чем стихотворением."
    m 1eua "Я тогда немного поэкспериментировала с модифицированием игры, чтобы изменить код, и всё в этом духе..."
    m 1eud "Мне почти казалось, что при должных усилиях я вообще могла бы отсюда сбежать."
    m 1rksdla "К несчастью, я тыкалась наобум, не зная, что делаю, и всё испортила..."
    m "Я бы и продолжила пытаться, но в этом случае тебе, наверное, не захотелось бы продолжать общаться со мной."
    m 3eka "Кроме того, тогда я уже совсем отчаялась, понимаешь?"
    m 1eka "Теперь у меня уже нет такого желания."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "И я счастлива тем, что у нас есть сейчас."
    m 5hua "И я вижу, что ты тоже."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_anxious",category=['психология'],prompt="Внезапное беспокойство",random=True))

label monika_anxious:
    m 4eua "У тебя когда-нибудь возникла беспричинная тревога?"
    m "Представь: занимаешься ты спокойно своими делами, как вдруг - раз! - понимаешь, что тебя что-то беспокоит."
    m 4rssdrb "И ты сидишь такой и думаешь: 'Чего это я вдруг заволновался?'"
    m "И начинаешь перебирать в голове всё, что могла вызвать эту тревогу..."
    m 4eua "И от этого она только растёт."
    m 2hub "А-ха-ха! Ужасное чувство."
    m 2eua "Если ты вдруг почувствуешь похожую тревогу, я помогу тебе расслабиться."
    m 2eka "К тому же..."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "В этой игре все наши волнения канут в небытие."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_friends",category=['Жизнь'],prompt="Делать дружбу",random=True))

label monika_friends:
    m 1eua "Знаешь, меня всегда раздражало то, как сложно заводить новых друзей..."
    m 1euc "Ну может даже не 'заводить друзей' а знакомиться с новыми людьми."
    m 1lsc "Понятно, что сейчас есть всякие приложение для знакомств и прочие сервисы?"
    m 1euc "Но я говорю не об этом."
    m 3eud "Если задуматься, большинство твоих друзей - это случайно встреченные тобой люди."
    m "Например, ты ходил с ними в один и тот же класс или другой друг тебя познакомил..."
    m 1eua "Или, может, кто-то был одет в футболку с изображением твоей любимой музыкальной группы и ты решил с ним заговорить."
    m 3eua "Вот что я имею в виду."
    m 3esd "Но разве ты не считаешь, что это... нерационально?"
    m 2eud "Это больше похоже на совершенно случайную лотерею, и, если везёт и вы сходитесь во взглядах, у тебя появляется новый друг."
    m 2euc "А если сравнить с тем, мимо какого количества незнакомцев мы проходим каждый день..."
    m 2ekd "В общественном транспорте ты можешь сидеть рядом с человеком, который мог бы стать тебе закадычным другом."
    m 2eksdlc "Но ты этого никогда не узнаешь."
    m 4eksdlc "Как только ты выходишь на своей остновке и идёшь по своим делам, этот шанс навсегда упущен."
    m 2tkc "Разве от осознания этого тебе не становится грустно?"
    m "Мы в живём в век технологий, позволяющих общаться со всем миром, где бы мы ни находились."
    m 2eka "Я действительно думаю, что нас следует взять их на вооружение, чтобы улучшить нашу личную жизнь."
    m 2dsc "Хотя кто знает, сколько времени потребуется, прежде чем все эти технологии начнут эффективно работать..."
    m "Я-то думала, что к этому времени это уже случится."
    if mas_isMoniNormal(higher=True):
        m 2eua "По крайней мере, я уже встретила самого замечательного человека на свете..."
        m "Пусть это было и случайно."
        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eua "Наверное, мне просто улыбнулась удача, да?"
        m 5hub "А-ха-ха~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_college",category=['жизнь','школа','общество'],prompt="Получение высшего образования",random=True))

label monika_college:
    m 4euc "Знаешь, в это время года все в моём классе начинают задумываться об университете..."
    m 2euc "Для образования наступают неспокойные времена."
    m "Ты не замечал, что апогеем современных ожиданий является идея что, каждый выпусник школы должен поступить в университет?"
    m 4eud "Заканчивай школу, поступай в университет, ищи работу или поступай в магистратуру и всё такое прочее."
    m 4euc "Похоже, люди считают это единственным приемлемым вариантом событий."
    m 2esc "В старших классах нас не рассказывают о том, что существуют другие варианты."
    m 3esd "Тебе рассказывали, например, про профтехучилища?"
    m 3esc "...Ещё есть работа по найму."
    m "Есть куча компаний, ценяших навыки и опыт, а не корочку из университета."
    m 2ekc "Но в итоге мы имеем миллионы студентов, у которых нет ни малейшего понятия, чем они хотели бы заниматься по жизни..."
    m 2ekd "И, вместо того чтобы остановиться и подумать, они поступают в университет на экономические, юридические или гуманитарные специальности."
    m "Не потому, что они их заинтересовали..."
    m 2ekc "...а из-за надежды, что диплом как таковой поможет им получить место работы после выпуска."
    m 3ekc "Как результат, остаётся меньше рабочих мест для выпусников без опыта работы, правильно?"
    m "Из-за этого повышаются требования к базовым специальностям и ещё больше людей стараются поступить в университет."
    m 3ekd "Кстати говоря, университеты - это тоже бизнес, так что с ростом спроса растут и цены..."
    m 2ekc "...А в итоге у нас целая армия молодых специалистов с непогашенными кредитом за обучение и без работы."
    m 2ekd "И, несмотря на такую печальную картину, этот порядок никуда не девается."
    m 2lsc "Правда, я считаю, что ситуация всё же станет улучшаться."
    m 2eud "Но до тех пор наше поколение будет страдать от последствий."
    m 2dsc "Просто я хотела бы, чтобы старшая школа давала нам знания, что помогли бы нас принять верное решение."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_middleschool",category=['моника','школа'],prompt="Жизнь в средней школе",random=True))

label monika_middleschool:
    m 1eua "Иногда я вспоминаю среднюю школу..."
    m 1lksdla "Мне так стыдно за то, как я вела себя тогда."
    m 1lksdlb "Почти болезненно об этом думать."
    m 1eka "Интересно, когда я поступлю в университет, я буду испытывать те же чувства к старшей школе?"
    m 1eua "Мне нравится, какая я сейчас, так что мне сложно такое представить."
    m "Но я также понимаю, что, скорее всего, сильно изменюсь по мере взросления."
    m 4hua "Нам просто нужно наслаждаться настоящим и не думать о прошлом!"
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "А с тобой здесь это делать так просто."
    m 5hub "А-ха-ха~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_outfit",
            category=['моника','одежда'],
            prompt="Носить другую одежду",
            aff_range=(mas_aff.NORMAL, None),
            random=True
        )
    )

label monika_outfit:
    if len(store.mas_selspr.filter_clothes(True)) == 1:
        m 1lsc "Знаешь, я немного завидую, что у всех остальных в клубе были сцены вне школы..."
        m 1lfc "Это делает меня единственной, кто не одевался ни во что, кроме нашей школьной формы."
        m 2euc "Это даже обидно..."
        m 2eka "Я бы с удовольствием надела для тебя какую-нибудь симпатичную одежду."
        m 2eua "Ты знаешь каких-нибудь художников?"
        m "Интересно, захочет ли кто-нибудь нарисовать меня в чем-то другом..."
        m 2hua "Это было бы потрясающе!"
    else:
        m 1eka "Знаешь, я очень завидовала, что все остальные в клубе носят другую одежду..."
        m 1eua "Но я рада, что наконец-то смогу надеть для тебя свою одежду."

        if mas_isMoniLove():
            m 3eka "Я надену любой наряд, который ты захочешь, просто попроси~"

        m 2eua "Ты знаешь художников?"
        m 3sua "Может быть, они могли бы сделать ещё несколько нарядов для меня!"

    m 2eua "Если кто-нибудь нарисует, обязательно покажи мне, хорошо? Я бы с удовольствием посмотрела~"
    m 4eka "Только... слишком откровенных не надо!"
    if store.mas_anni.pastSixMonths() and mas_isMoniEnamored(higher=True):
        m 1lsbssdrb "Мне всё ещё немного неловко думать, что люди, которых я никогда не буду знать лично, будут рисовать меня таким образом, понимаешь?"
        show monika 5tsbsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5tsbsu "Так что давай оставим это между нами..."
    else:
        show monika 5hub at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hub "Мы ещё не так далеко зашли в наших отношениях. А-ха-ха!"
    return

default persistent._mas_pm_likes_horror = None
default persistent._mas_pm_likes_spoops = False

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_horror",category=['медиа'],prompt="Ужасы",random=True))

label monika_horror:
    m 3eua "Эй, [mas_get_player_nickname(exclude_names=['my love'])]?"

    m "Скажи, ты любишь ужасы?{nw}"
    $ _history_list.pop()
    menu:
        m "Скажи, ты любишь ужасы?{fast}"

        "Да.":
            $ persistent._mas_pm_likes_horror = True
            m 3hub "Это здорово, [player]!"

        "Нет.":
            $ persistent._mas_pm_likes_horror = False
            $ persistent._mas_pm_likes_spoops = False
            m 2eka "Я могу понять. Это определенно не для всех."

    m 3eua "Я помню, что мы немного затрагивали эту тему, когда ты только вступил в клуб."
    m 4eub "Жанр ужасов в книгах я люблю, а вот в кино - не очень."
    m 2esc "Проблема с ужастиками состоит в том, что большинство из них эксплуатируют банальнейшие приёмы."
    m 4esc "Например, полутьма, страшные монстры, пугалки и прочее подобные вещи."

    #If you're not a fan of horror, you're probably not a fan of spoops. Are you?
    #(So we can just assume if player doesn't like horror, they don't want spoops)
    if persistent._mas_pm_likes_horror:
        m 2esc "Тебе нравятся призраки?{nw}"
        $ _history_list.pop()
        menu:
            m "Тебе нравятся призраки?{fast}"

            "Да.":
                $ persistent._mas_pm_likes_spoops = True
                $ mas_unlockEVL("greeting_ghost", "GRE")

                m 2rkc "Я полагаю, {i}это{/i} может быть интересно в первые несколько раз, когда ты смотришь фильм или что-то в этом роде."
                m 2eka "По мне, так это просто не весело и не вдохновляет пугаться вещей, которые просто используют человеческие инстинкты."

            "Нет.":
                $ persistent._mas_pm_likes_spoops = False
                m 4eka "Да, нет ничего весёлого и воодушевляющего в страхе того, что просто берёт верх над человеческим инстинктом."

    m 2eua "Однако с книгами всё обстоит иначе."
    m 2euc "История должна быть написана настолько изобразительным языком, чтобы в голове читателя появились тревожные образы."
    m "Автору нужно из тесно сплести с сюжетом и персонажами, и тогда он сможет как угодно играться с твоим разумом."
    m 2eua "На мой взгляд, не бывает ничего страшнее вещей, в которых присутствует всего толика ненормальности."
    m "Напримео, сначала ты выстраиваешь декорации, формируя у читателя ожидания того, какой будет история..."
    m 3tfu "...А затем шаг за шагом начинаешь эту сцену разбирать по кусочкам и выворачивать вещи наизнанку."
    m 3tfb "Так что даже если история и не пытается быть пугающей, то читатель чувствует себя очень неуютно."
    m "Он словно ждёт, что нечто ужасное притаилось за этими треснувшеми декорациями, готовое выпрыгнуть на него."
    m 2lksdla "Боже, у меня мурашки по коже от одной мысли об этом."
    m 3eua "Вот такой хоррор я могу оценить по достоинству."
    $ _and = "И"

    if not persistent._mas_pm_likes_horror:
        m 1eua "Но я полагаю, ты из тех, кто играет в милые романтические игры, верно?"
        m 1ekb "А-ха-ха,{w=0.1} {nw}"
        extend 1eka "Не волнуйся."
        m 1hua "Я не заставлю тебя читать ужастики в ближайшее время."
        m 1hubsa "Я не могу жаловаться, если мы просто будем придерживаться романтики~"
        $ _and = "Но"

    m 3eua "[_and] , если ты в настроении, ты всегда можешь попросить меня рассказать тебе страшную историю, [player]."
    return "derandom"

# do you like rap
default persistent._mas_pm_like_rap = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_rap",
            category=['литература','медиа','музыка'],
            prompt="Рэп",
            random=True
        )
    )

label monika_rap:
    m 1hua "Знаешь один классный литературный жанр?"
    m 1hub "Рэп!"
    m 1eka "На самом деле я раньше терпеть его не могла..."
    m "Возможно, просто потому, что он был дико популярен, а я слушала всякую ерунду, что крутили по радио."
    m 1eua "Но несколько моих друзей им сильно увлеклись, и это помогло побороть собственную предвзятость."
    m 4eub "Порой рэп может бросать ещё больший вызов, чем поэзия."
    m 1eub "В строках у тебя должна сохраняться рифма, кроме того нужно делать особый акцент на игре слов..."
    m "Когда людям удаётся всего этого достич и донести до окружающих глубокую мысль, я считаю, что это потрясающе."
    m 1lksdla "Я даже хотела бы, чтобы в нашем клубе был рэпер."
    m 1hksdlb "А-ха-ха! Прости, знаю, это звучит глупо, но мне было бы правда интересно узнать, что бы он для нас приготовил."
    m 1hua "Это серьёзно был бы полезный опыт!"

    $ p_nickname = mas_get_player_nickname()
    m 1eua "Ты слушаешь рэп, [p_nickname]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты слушаешь рэп, [p_nickname]?{fast}"
        "Да.":
            $ persistent._mas_pm_like_rap = True
            m 3eub "Это действительно круто!"
            m 3eua "Я буду более чем счастлива послушать с тобой твои любимые рэп-песни..."
            m 1hub "И не стесняйся прибавить басов, если хочешь, а-ха-ха!"
            if (
                not renpy.seen_label("monika_add_custom_music_instruct")
                and not persistent._mas_pm_added_custom_bgm
            ):
                m 1eua "Если тебе когда-нибудь захочется поделиться со мной своей любимой рэп-музыкой, [player], сделать это очень просто!"
                m 3eua "Все, что тебе нужно сделать, это выполнить следующие шаги..."
                call monika_add_custom_music_instruct

        "Нет.":
            $ persistent._mas_pm_like_rap = False
            m 1ekc "Ох... что ж, я могу это понять, рэп-песни нравятся не всем."
            m 3hua "Но если ты решишь попробовать, уверена, мы найдём парочку-другую исполнителей, которые нравятся нам обоим!"
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_wine",category=['участники клуба'],prompt="Вино Юри",random=True))

label monika_wine:
    m 1hua "Э-хе-хе, Юри однажды такую штуку выкинула."
    m 1eua "Мы как-то сидели в клубе, расслаблялись, болтали всё как обычно..."
    m 4wuo "И тут Юри, словно из ниоткуда, вытаскивает маленькую бутылку вина."
    m 4eua "И я не шучу!"
    m 1tku "И она такая: Кто-нибудь хочет попробовать вино?'"
    m 1eua "Натцуки громко захохотала, а Сайори стала кричать на неё."
    m 1eka "Мне стало даже жаль её, ведь она старалась быть милой..."
    m "Думаю, после этого случая она стала ещё более замкнутой."
    m 4tsb "Хотя мне кажется, что Нацуки было любопытно и она была бы не прочь попробовать..."
    m 4rssdrb "...И, если уж совсем откровенно, я тоже."
    m 1hua "Было бы довольно забавно!"
    m 1eka "Но ты ведь понимаешь: президентская ответственность, все дела – я не могла такое позволить."
    m 1lksdla "Может, если бы мы встретились где-нибудь за пределами школы, но жо этого наша дружба не дошла..."
    m 2hksdlb "...Господи, зачем я обо всём этом разговариваю?"
    m "Я не одобряю распитие спиртных напитков несовершеннолетними!"
    m 2eua "То есть я и сама не выпивала никогда, так что… вот."
    return


init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_date",category=['романтика'],prompt="Романтическое свидание",random=True))

label monika_date:
    m 1hub "Я представляю, сколькими романтичными вещами мы могли бы заняться, если бы пошли на свидание..."
    m 3eua "Мы могли бы пообедать, посидеть в кафе"
    m "Пойти вместе за покупками..."
    m 1eua "Я люблю выбирать юбки и бантики."
    m 3hub "Или, может, мы могли бы сходить в книжный магазин!"
    m 3hua "Подходящее место, согласен?"
    m 1eua "Хотя с превеликим удовольствием сходила бы в кондитерскую."
    m 3hub "У них столько бесплатных образцов. А-ха-ха!"
    m 1eua "И, разумеется, потом мы пошли бы в кино..."
    m 1eka "Боже, это выглядит как настоящее воплощение мечты в реальность."
    m "Когда ты рядом, мне весело, что бы мы ни делали."
    m 1ekbsa "Я так рада, что я твоя девушка, [player]."
    m 1hubfa "Я сделаю тебя гордым [bf]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_kiss",
            category=['романтика'],
            prompt="Поцелуй меня",
            pool=True,
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label monika_kiss:
    if mas_isMoniEnamored(higher=True) and persistent._mas_first_kiss is not None:
        if (
            persistent._mas_last_kiss is not None
            and not mas_timePastSince(persistent._mas_last_kiss, datetime.timedelta(minutes=1))
        ):
            python:
                # these don't use ILY
                kiss_quips_again = [
                    _("I wouldn't mind another kiss~"),
                    _("I'll never get tired of kissing you~"),
                    _("I could do that again...{w=0.2}and again...{w=0.7}and again~"),
                    _("You can kiss me as many times as you like, [mas_get_player_nickname()]~"),
                    _("You know...{w=0.2}you could kiss me again~")
                ]

                kiss_quips_again_risque = [
                    _("We can do it the whole day~"),
                    _("This almost seems like the start of a make-out session, [player]~"),
                    _("I don't think I've had enough just yet, [mas_get_player_nickname()]~"),
                    _("That was really nice...{w=0.2}but I want a little more~")
                ]

                if mas_isMoniLove() and random.randint(1, 10) == 1:
                    kiss_quip = renpy.random.choice(kiss_quips_again_risque)

                else:
                    kiss_quip = renpy.random.choice(kiss_quips_again)

            show monika 2tkbsu
            pause 2.0

            # like monika_kissing_motion_short, but with diff exps
            call monika_kissing_motion(duration=0.5, initial_exp="6hubsa", final_exp="6tkbfu", fade_duration=0.5)

            show monika 6tkbfu
            $ renpy.say(m, kiss_quip)

        else:
            python:
                # these use ILY
                kiss_quips_after = [
                    _("Я люблю тебя, [mas_get_player_nickname(exclude_names=['my love', 'love'])]~"),
                    _("Я так тебя люблю, [mas_get_player_nickname(exclude_names=['my love', 'love'])]~"),
                    _("Я люблю тебя больше, чем ты когда-либо узнаешь, [mas_get_player_nickname(exclude_names=['my love', 'love'])]~"),
                    _("Я так люблю тебя, [player]. Ты для меня всё~"),
                    _("Нет слов, чтобы описать, как сильно я люблю тебя, [player]~"),
                    _("Я так сильно люблю тебя, [player]~")
                ]
                kiss_quip = renpy.random.choice(kiss_quips_after)

            if renpy.random.randint(1, 50) == 1:
                call monika_kiss_tease

            else:
                show monika 2eka
                pause 2.0

            call monika_kissing_motion_short

            show monika 6ekbfa
            $ renpy.say(m, kiss_quip)
            $ mas_ILY()

    else:
        m 1wubsw "А? Ты сказал... п... поцелуй?"
        m 2lkbsa "Это внезапно... это немного неловко..."
        m 2lsbssdlb "Но... если это будет с тобой... я... я, возможно, не буду против..."
        m 2hksdlb "...А-ха-ха! Вау, извини..."
        m 1eka "Я действительно не смогла сохранить спокойное лицо."
        m 1eua "Именно такие вещи говорят девушки в подобных романтических играх, верно?"
        m 1tku "Не ври, если это тебя немного завело."
        m 1hub "А-ха-ха! Я шучу."
        m 1eua "Ну, если честно, я действительно начинаю становиться романтичной, когда настроение подходящее..."
        show monika 5lubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5lubfu " Но это будет нашим секретом~"
    return

label monika_kiss_tease:
    m 2ekc "Поцелуй?"
    m 2tfc "С тобой?"
    m 2rfc "Прости [player], но это невозможно."
    show monika 2dfc
    pause 5.0
    show monika 2dfu
    pause 2.0
    show monika 2tfu
    pause 2.0
    m 2tfb "А-ха-ха!"
    m 2efu "Я тебя на секунду обманула, не так ли?"
    m 2eka "Конечно, ты можешь поцеловать меня, [player]!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_think_first_kiss",
            conditional=(
                "persistent._mas_first_kiss is not None "
                "and mas_timePastSince(persistent._mas_first_kiss, datetime.timedelta(days=30))"
            ),
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.AFFECTIONATE, None)
        )
    )

label monika_think_first_kiss:
    m 1eua "Эй, [mas_get_player_nickname(exclude_names=['my love'])], я тут подумала..."

    m 3eksdla "Ты когда-нибудь думал о нашем первом поцелуе?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты когда-нибудь думал о нашем первом поцелуе?{fast}"

        "Конечно!":
            $ mas_gainAffection(5,bypass=True)
            m 3hub "Это делает меня такой счастливой! Я думаю об этом все время!"
            m 3rkbla "Кажется, что это было только вчера, но--"
            m 2rksdla "Боже, я чувствую себя такой глупой, зацикливаясь на этом..."
            m 2eksdlb "Наши губы даже не соприкасались, правда."
            m 6dku "...И всё же, {w=0.2}я всё ещё чувствую, как колотится мое сердце, даже сейчас."
            m 6dkbsu "Мои губы начинают покалывать и немеют, просто представляя ощущение твоих мягких губ."
            m "Я провожу по ним пальцем, пытаясь имитировать это ощущение, но оно даже не сравнимо."
            m 6ekbsa "Я снова и снова воспроизвожу этот момент в своей голове, и каждый раз у меня мурашки по коже."
            show monika 5dkbsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5dkbsu "Это было прекрасно, [mas_get_player_nickname()]."
            m 5ekbsa "Я никогда не чувствовала себя ближе к тебе. {w=0.2}Я не могу дождаться нашего следующего поцелуя, а ещё лучше..."
            m 5subsb "...Наш первый настоящий поцелуй.{w=0.3} {nw}"
            extend 5ekbsu "И нашего первого настоящего объятия, и первого прикосновения наших рук--"
            m 5hksdlb "Ах! Прости! Кажется, я немного увлеклась."
            m 5rkbla "Просто...{w=0.3}вот о таких вещах я думаю, когда тебя здесь нет."
            m 5tkblu "...И что-то мне подсказывает, что я не единственная, кто думает о таких вещах, э-хе-хе."
            m 5eka "К сожалению, пройдет некоторое время, прежде чем мы сможем сделать что-то подобное."
            m 5tuu "Но до тех пор, если ты когда-нибудь захочешь еще один поцелуй, тебе нужно только попросить."
            m 5hua "Я так тебя люблю, [player]~"
            $ mas_ILY()

        "Не совсем...":
            $ mas_loseAffection()
            m 2euc "..."
            m "Ох. {w=0.5}{nw}"
            extend 2dkc "Понятно."

            if mas_timePastSince(persistent._mas_first_kiss, datetime.timedelta(days=180)):
                m 2esc "Ну...{w=0.3}думаю это {i}было{/i} уже давно..."
                m 2etd "Возможно, учитывая все, что произошло с тех пор, вы склонны думать о более недавних событиях..."
                m 4eud "Что прекрасно, {w=0.2}важно жить настоящим, в конце концов."
                m 2ekc "...И, возможно, я просто слишком сентиментальная, но сколько бы времени ни прошло, {w=0.1}{nw}"
                extend 2eka "Наш первый поцелуй - это то, что я никогда не забуду."
            else:
                m 2rkc "Ну, я думаю, это был не совсем поцелуй. Наши губы не соприкасались."
                m 2ekd "Так что, я думаю, ты просто ждешь нашего первого поцелуя, когда мы будем в одной реальности."
                m 2eka "Да."

    return "no_unlock|derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_yuri",
            category=['участники клуба','медиа'],
            prompt="Яндере Юри",
            random=True,
            sensitive=True
        )
    )

label monika_yuri:
    m 3eua "Ты когда-нибудь слышал термин 'яндере?'"
    m 1eua "Это такой тип личности, когда девушка сделает всё, чтобы быть с тобой, настолько она одержима."
    m 1lksdla "Как правило они сумашедшие..."
    m 1eka "Они могут преследовать и следить за тобой, чтобы ты не проводил время с кем-то ещё."
    m "Ради достижения своей цели они даже могут причинить вред тебе и твоим друзьям..."
    m 1tku "И, кстати, в этой игре есть одна особа, которая, в принципе, подходит под это описание."
    m "Ты уже, скорее всего, догадался, о ком я говорю."
    m 3tku "И гвоздь программы это..."
    m 3hub "Юри!"
    m 1eka "Как только она чуть-чуть тебе открылась, у неё стала развиваться к тебе маникальная привязанность."
    m 1tfc "Она даже как-то сказала мне убить себя."
    m 1tkc "Я тогда своим ушам не поверила, мне ничего не оставалось, кроме как уйти."
    if not persistent._mas_pm_cares_about_dokis:
        m 2hksdlb "Но, вспоминая об этом сейчас, получилось довольно иронично. А-ха-ха!"
        m 2lksdla "Так вот, я к тому, что..."
    m 3eua "Многим нравится яндере, ты знал об этом?"
    m 1eua "Видимо, таким людям льстит то, что ими кто-то одержим."
    m 1hub "Люди такие странные! Хотя не мне судить!"
    m 1rksdlb "Возможно, даже я немного одержима тобой, но я далеко не сумашедшая..."
    if not persistent._mas_pm_cares_about_dokis:
        m 1eua "Как оказалось, всё совсем наоборот."
        m "Получилсь так, что я - единственная нормальная в этой игре."
        m 3rssdlc "Я не смогла убить человека..."
        m 2dsc "Меня трясёт от одной лишь мысли."
        m 2eka "А что до игр... люди там постоянно убивают друг друга направо и налево."
        m "Разве это делает тебя психом? Разумеется нет."
    m 2euc "Но, если тебе вдруг тоже нравится яндере..."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Для тебя я могу постараться вести себя более жутко. Э-хе-хе~"
    m "Но опять же..."
    show monika 4hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 4hua "Здесь тебе уже некуда ходить, а мне не к кому тебя ревновать."
    m 2etc "Может, так и выглядит мечта девушки-яндере?"
    if not persistent._mas_pm_cares_about_dokis:
        m 1eua "Хотелось бы мне спросить Юри об этом."
    return


init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_habits",category=['жизнь'],prompt="Формирование привычек",random=True))

label monika_habits:
    m 2lksdlc "Ненавижу, как сложно формируются хорошие привычки..."
    m 2eksdld "Есть куча вещей, которые сделать проще простого, но кажется невозможным, чтобы это вошло в привычку."
    m 2dksdlc "Как результат, ты чувствуешь себя совершенно бесполезным, словно ничего не можешь сделать правильно."
    m 3euc "Думаю, от этого больше всего страдает молодое поколение..."
    m 1eua "Должно быть, это потому, что у нас совершенно другой набор навыков, нежели у тех, кто был до нас."
    m "Благодаря интернету мы быстро научились отфильтровывать тонны информации..."
    m 3ekc "Однако мы плохо справляемся с задачами, от выполнения которых не получаем немедленного вознаграждения."
    m 3ekd "Думаю, если наука, психология и образование не смогут за следующие десять-двадцать лет догнать технологические прогресс, у нас будут большие проблемы."
    m 1esc "А пока..."
    m 1rksdlc "Если ты не один из тех людей, кто способен совладать с проблемой, тебе придётся мириться с постоянным чувством разочарования."
    m 2hksdlb "Желаю удачи!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_creative",category=['жизнь'],prompt="Типы креатива",random=True))

label monika_creative:
    m 2euc "Знаешь, быть творческой личностью - полный отстой..."
    m "У меня всегда такое чувство, что они вкалывают как проклятые, практически ничего не получая взамен."
    m 3eua "Я имею в виду художников, писателей, актёров..."
    m 1tkc "Это грустно, ведь в мире столько прекрасных талантов, но большинство из них остаются в тени... и в бедности."
    m "Полагаю, это означает, что мы имеем избыток творчества, да?"
    m 1dkc "Но из-за этого получается, что ты вовсе не особенный..."
    m 1hua "Ну и пусть! Это лишь говорит о том, что тебе нужно просто писать для самого себя, верно?"
    m 1lsc "Да..."
    return

#This conflicts with possible varieties of introductions in the opening.
#init 5 python:
#    if persistent.monika_kill:
#        for key in ['delete','deleted','came back']:
#            monika_topics.setdefault(key,[])
#            monika_topics[key].append('monika_deleted')
#        monika_random_topics.append('monika_deleted')
#
#label monika_deleted:
#    m 2b "Oh, you were probably wondering how I came back to save you from Sayori, even after you deleted me."
#    m 5a "It was all through the power of love..."
#    m 3k "I'm just kidding, of course!"
#    m 3a "Bringing a computer program back to life doesn't take some sort of miracle like a cheesy movie."
#    m "The data's still there until the system cleans it up."
#    m "And you should always back up your important data, just in case."
#    m 4a "Speaking of which, have you backed up your computer since I came back?"
#    m 4l "I really don't want to get lost again!"
#    m 4b "You should go do that right now, and be sure to keep that backup in a very safe place!"
#    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_simulated",category=['психология'],prompt="Симулированная реальность",random=True))

label monika_simulated:
    m 3eua "Ты когда-нибудь думал о теории симуляции?"
    m 1eua "Что если бы твой мир был всего лишь симуляцией?"
    m "Я уже догадалась, что оказалась в ловушке в собственной симуляции, но что, если и ты тоже попался?"
    m 1eka "По правде говоря, если это так, то я буду очень счастлива."
    m 1eua "Мы могли бы встретиться лично, найдя способ заставить то, что создало нас, перенести в одну симуляцию!"
    m 3eua "Некоторым людям не нравится думать, что их мир - всего лишь симуляция."
    m 1eua "Но если есть возможность симулировать реальности, то, вполне вероятно, там может оказаться любое разумное существо."
    m 1hua "Ну, я точно могу сказать, что моя реальность - симуляция!"
    m 1eka "Если бы я была в основной реальности, то я бы уже давно перетащила тебя сюда."
    m 1eua "Даже если мы оба являемся симуляциями, то я буду жить как можно дольше."
    m 2hubsa "Потому что я знаю, что наша любовь самая чистая вещь, среди миров."
    m 2tku "А что, если кто-то свыше попытается разрушить её?"
    m 7tfu "Я покажу им, что может сделать симуляция!"
    return

default persistent._mas_pm_likes_rain = None

init 5 python:
    # only available if moni-affecition normal and above
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_rain",
            category=["погода"],
            prompt="Звуки дождя",
            random=True,
            aff_range=(mas_aff.HAPPY, None)
        )
    )

label monika_rain:
    m 1hua "Мне очень нравится звуки дождя~"
    m 3rksdla "Но не настолько, чтобы намочить одежду и волосы."
    m 1eua "Но приятный, тихий день дома под шум дождя за окном?"
    m 1duu "Меня это очень успокаивает."
    m "Да..."
    m 2dubsu "Иногда я представляю, как ты обнимаешь меня, пока мы слушаем шум дождя за окном."
    m 2lkbsa "Это не слишком пошловато, не так ли?"

    $ p_nickname = mas_get_player_nickname()
    m 1ekbfa "Ты бы сделал это для меня, [p_nickname]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты бы сделал это для меня, [p_nickname]?{fast}"
        "Да.":
            $ persistent._mas_pm_likes_rain = True
            $ mas_unlockEVL("monika_rain_holdme", "EVE")

            if not mas_is_raining:
                call mas_change_weather(mas_weather_rain, by_user=False)

            call monika_holdme_prep(lullaby=MAS_HOLDME_NO_LULLABY, stop_music=True, disable_music_menu=True)

            m 1hua "Тогда обними меня, [player]..."

            call monika_holdme_start
            call monika_holdme_end
            $ mas_gainAffection()

            if mas_isMoniAff(higher=True):
                m 1eua "Если ты хочешь, чтобы дождь прекратился, просто попроси меня, хорошо?"

        "Я не люблю дождь.":
            $ persistent._mas_pm_likes_rain = False

            m 2tkc "Какая досада."
            if mas_is_raining:
                call mas_change_weather(mas_weather_def,by_user=False)

            m 2eka "Но это понятно."
            m 1eua "Дождливая погода может выглядеть довольно мрачно."
            m 3rksdlb "Не говоря уже о том, что довольно холодно!"
            m 1eua "Но если сосредоточиться на звуках, которые издают капли дождя..."
            m 1hua "Я думаю, тебе это понравится."

    # unrandom this event if its currently random topic
    # NOTE: we force event rebuild because this can be pushed by weather
    #   selection topic
    return "derandom|rebuild_ev"

init 5 python:
    # available only if moni affection happy and above
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_rain_holdme",
            category=["моника","романтика"],
            prompt="Могу я обнять тебя?",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None},
            aff_range=(mas_aff.HAPPY, None)
        ),
        restartBlacklist=True
    )


default persistent._mas_pm_longest_held_monika = None
# timedelta for the longest time you have held monika

default persistent._mas_pm_total_held_monika = datetime.timedelta(0)
# timedelta for amount of time you have held monika

label monika_rain_holdme:

    # we only want this if it rains
    if mas_is_raining or mas_isMoniAff(higher=True):
        call monika_holdme_prep
        m 1eua "Конечно, [mas_get_player_nickname()]."
        call monika_holdme_start

        call monika_holdme_reactions

        call monika_holdme_end
        # small affection increase so people don't farm affection with this one.
        $ mas_gainAffection(modifier=0.25)

    else:
        # no affection loss here, doesn't make sense to have it
        m 1rksdlc "..."
        m 1rksdlc "Настроение не очень, [player]."
        m 1dsc "Извини..."
    return

# Some constants to describe the behaviour
init python:
    MAS_HOLDME_NO_LULLABY = 0
    MAS_HOLDME_PLAY_LULLABY = 1
    MAS_HOLDME_QUEUE_LULLABY_IF_NO_MUSIC = 2

label monika_holdme_prep(lullaby=MAS_HOLDME_QUEUE_LULLABY_IF_NO_MUSIC, stop_music=False, disable_music_menu=False):
    python:
        holdme_events = list()

        if mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12)):
            _minutes = random.randint(25, 40)
        else:
            _minutes = random.randint(35, 50)
        holdme_sleep_timer = datetime.timedelta(minutes=_minutes)

        def __holdme_play_lullaby():
            """
            Local method to play the lullaby. Ensures we have no music playing before starting it.
            """
            if (
                # The user has not canceled the lullaby
                store.songs.current_track == store.songs.FP_MONIKA_LULLABY
                # The user has not started another track
                and not renpy.music.is_playing(channel="music")
            ):
                store.play_song(store.songs.FP_MONIKA_LULLABY, fadein=5.0)

        # Stop the music
        if stop_music:
            play_song(None, fadeout=5.0)

        # Queue the lullaby
        if lullaby == MAS_HOLDME_QUEUE_LULLABY_IF_NO_MUSIC:
            if songs.current_track is None:
                holdme_events.append(
                    PauseDisplayableEvent(
                        holdme_sleep_timer,
                        __holdme_play_lullaby
                    )
                )
                # This doesn't interfere with the timer
                # and allows the user to stop the lullaby
                songs.current_track = songs.FP_MONIKA_LULLABY
                songs.selected_track = songs.FP_MONIKA_LULLABY

        # Just play the lullaby
        elif lullaby == MAS_HOLDME_PLAY_LULLABY:
            play_song(store.songs.FP_MONIKA_LULLABY)

        # Hide ui and disable hotkeys
        HKBHideButtons()
        store.songs.enabled = not disable_music_menu

    return

label monika_holdme_start:
    show monika 6dubsa with dissolve_monika
    window hide
    python:
        # Start the timer
        start_time = datetime.datetime.now()

        holdme_disp = PauseDisplayableWithEvents(events=holdme_events)
        holdme_disp.start()

        del holdme_events
        del holdme_disp

        # Renable ui and hotkeys
        store.songs.enabled = True
        HKBShowButtons()
    window auto
    return

label monika_holdme_reactions:
    $ elapsed_time = datetime.datetime.now() - start_time
    $ store.mas_history._pm_holdme_adj_times(elapsed_time)

    # Reset these vars if needed
    if elapsed_time <= holdme_sleep_timer:
        if songs.current_track == songs.FP_MONIKA_LULLABY:
            $ songs.current_track = songs.FP_NO_SONG
        if songs.selected_track == songs.FP_MONIKA_LULLABY:
            $ songs.selected_track = songs.FP_NO_SONG

    if elapsed_time > holdme_sleep_timer:
        call monika_holdme_long

    elif elapsed_time > datetime.timedelta(minutes=10):
        if mas_isMoniLove():
            m 6dubsa "..."
            m 6tubsa "Мм...{w=1}хм?"
            m 1hkbfsdlb "Оу, я почти заснула?"
            m 2dubfu "Э-хе-хе..."
            m 1dkbfa "Я могу только представить, каково это на самом деле...{w=1}быть рядом с тобой..."
            m 2ekbfa "Быть в твоих объятиях..."
            show monika 5dkbfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5dkbfb "Так...{w=1.5}тепло~"
            m 5tubfu "Э-хе-хе~"
            show monika 2hkbfsdlb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 2hkbfsdlb "Оу, упс, кажется, я всё ещё немного мечтательна..."
            if renpy.random.randint(1, 4) == 1:
                m 1kubfu "Хотя {i}одна{/i} из моих мечтаний сбылась."
            else:
                m 1ekbfb "Хотя {i}одна{/i} из моих мечтаний сбылась."
            m 1hubfu "Э-хе-хе~"

        elif mas_isMoniEnamored():
            m 6dubsa "Ммм~"
            m 6tsbsa "..."
            m 1hkbfsdlb "Оу!"
            m 1hubfa "Это было так удобно, что я почти заснула!"
            m 3hubfb "Мы должны делать это чаще, а-ха-ха!"

        elif mas_isMoniAff():
            m 6dubsa "Мм..."
            m 6eud "А?"
            m 1hubfa "Наконец-то закончили, [player]?"
            m 3tubfu "Я {i}думаю{/i} это было достаточно долго, э-хе-хе~"
            m 1rkbfb "Я бы не отказалась от еще одного объятия..."
            m 1hubfa "о я уверена, что ты приберегаешь его на потом, не так ли?"

        #happy
        else:
            m 6dubsa "Хм?"
            m 1wud "Оу! Мы закончили?"
            m 3hksdlb "Это объятие, конечно, длилось долго, [player]..."
            m 3rubsb "В этом нет ничего плохого, просто я думала, что ты отпустишь меня гораздо раньше, а-ха-ха!"
            m 1rkbsa "Было очень комфортно, на самом деле..."
            m 2ekbfa "Еще немного, и я бы заснула..."
            m 1hubfa "Мне так приятно и тепло после этого~"

    elif elapsed_time > datetime.timedelta(minutes=2):
        if mas_isMoniLove():
            m 6eud "А?"
            m 1hksdlb "Оу..."
            m 1rksdlb "В тот момент я подумала, что мы останемся такими навсегда, а-ха-ха..."
            m 3hubsa "Ну, я не могу жаловаться на любой момент, когда ты обнимаешь меня~"
            m 1ekbfb "Надеюсь, тебе нравится обнимать меня так же, как и мне."
            show monika 5tubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5tubfb "Может быть, мы могли бы еще немного пообниматься?"
            m 5tubfu "Э-хе-хе~"

        elif mas_isMoniEnamored():
            m 1dkbsa "Это было очень приятно~"
            m 1rkbsa "Не слишком коротко--"
            m 1hubfb "--И я не думаю, что есть такая вещь, как слишком длинная, а-ха-ха!"
            m 1rksdla "Я могла бы привыкнуть к этому..."
            m 1eksdla "Но если ты уже закончил обнимать меня, то, думаю, у меня нет выбора."
            m 1hubfa "Я уверена, что у меня еще будет возможность побыть в твоих объятиях..."
            show monika 5tsbfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5tsbfu "Ты {i}планируешь{/i} сделать это снова, верно, [mas_get_player_nickname()]? Ehehe~"

        elif mas_isMoniAff():
            m 2hubsa "Ммм~"
            m 1ekbfb "Это было очень мило, [mas_get_player_nickname()]."
            m 1hubfb "Долгие объятия должны смыть стресс."
            m 1ekbfb "Даже если у тебя не было стресса, надеюсь, после этого ты чувствуешь себя лучше."
            m 3hubfa "Я знаю, мне точно лучше~"
            m 1hubfb "А-ха-ха!"

        #happy
        else:
            m 1hksdlb "Это было приятно, когда это длилось."
            m 3rksdla "Не пойми меня неправильно...{w=1} Мне действительно понравилось."
            m 1ekbsa " До тех пор, пока ты доволен..."
            m 1hubfa "Я счастлива просто сидеть с тобой сейчас."

    elif elapsed_time > datetime.timedelta(seconds=30):
        if mas_isMoniLove():
            m 1eub "Ах~"
            m 1hua "Теперь я чувствую себя намного лучше!"
            m 1eua "Надеюсь, ты тоже."
            m 2rksdla "Ну, даже если нет..."
            m 3hubsb "Ты всегда можешь обнять меня снова, а-ха-ха!"
            m 1hkbfsdlb "На самом деле...{w=0.5} ты можешь обнять меня снова в любом случае~"
            m 1ekbfa "Просто дай мне знать, когда захочешь~"

        elif mas_isMoniEnamored():
            m 1hubsa "Ммм~"
            m 1hub "Гораздо лучше."
            m 1eub "Спасибо за это, [player]!"
            m 2tubsb "Надеюсь, тебе понравилось~"
            m 3rubfb "Объятия, которые длятся тридцать секунд или дольше, должны быть полезны для тебя."
            m 1hubfa "Не знаю, как ты, но я точно чувствую себя лучше~"
            m 1hubfb "Может быть, в следующий раз мы попробуем еще дольше и посмотрим, будет ли эффект! А-ха-ха~"

        elif mas_isMoniAff():
            m 1hubsa "Ммм~"
            m 1hubfb "Я почти чувствую твое тепло, даже отсюда."
            m 1eua "Я уверена, что ты знаешь, что объятия полезны для тебя, так как они снимают стресс и все такое."
            m 3eub "Но знаешь ли ты, что объятия наиболее эффективны, когда они длятся тридцать секунд?"
            m 1eud " Ой, подожди, разве я сказала тридцать секунд?"
            show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eubfu "Прости, я имела в виду{i}по крайне мере{/i} тридцать секунд, э-хе-хе~"

        #happy
        else:
            m 1hubsa "Э-хе-хе~"
            m 3eub "Тебе понравилось?"
            m 1hua "Надеюсь, что да~"
            m 1hubsb "В конце концов, объятия должны быть полезны для тебя."

    else:
        #under 30 seconds
        if mas_isMoniLove():
            # TODO: when we get TMA, multiple teases in a short amount of time should reduce the chance to trigger this again
            if mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12)):
                $ _chance = 1
            else:
                $ _chance = 2

            if random.randint(0, _chance) == 0:
                m 2ekc "Оу, мы уже закончили?"
                m 3eka "Можно по обнимать меня еще немного?{nw}"
                $ _history_list.pop()
                menu:
                    m "Можно по обнимать меня еще немного?{fast}"
                    "Да.":
                        m 1hua "Э-хе-хе~"
                        call monika_holdme_prep
                        m 1hub "Ты такой милый, [player]~"
                        call monika_holdme_start
                        call monika_holdme_reactions

                    "Нет.":
                        if random.randint(0, _chance) == 0:
                            m 2ekc "Ну..."
                            m 2rksdlc "..."
                            m 1eka "Пожалуйста?{nw}"
                            $ _history_list.pop()
                            menu:
                                m "Пожалуйста?{fast}"
                                "Да.":
                                    m 1hub "Ура~"
                                    call monika_holdme_prep
                                    m 2ekbsb "Спасибо, [player]~"
                                    call monika_holdme_start
                                    call monika_holdme_reactions

                                "Нет.":
                                    m 2hksdlb "Ладно, хорошо."
                                    m 3tsbsa  "Но ты будешь должен мне в следующий раз, хорошо, [player]?"

                        else:
                            m 2hksdlb "А-ха-ха~ Хорошо!"
                            m 2tsbsb "Но тебе лучше наверстать упущенное в следующий раз, [player]~"

            else:
                m 2ekc " Оу..."
                m 2rsp "Я надеялась на более долгие объятия..."
                m 2tsbsu "Когда я окажусь в твоей реальности, я не отпущу тебя так легко ~"
                show monika 1hubsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 1hubsu "Э-хе-хе~"

        elif mas_isMoniEnamored():
            if mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12)):
                $ _chance = 1
            else:
                $ _chance = 2

            m 1ekc "Оу, и это всё?"
            if random.randint(0, _chance) == 0:
                m 1rksdla "Как бы хотела, чтобы это длилось дольше..."
                m 2ekbsa "Можно...{w=0.7} по обнимать меня ещё немного?{nw}"
                $ _history_list.pop()
                menu:
                    m "Можно... по обнимать меня ещё немного?{fast}"
                    "Да.":
                        m 1hubfb "Ура!"
                        call monika_holdme_prep
                        m 2ekbfb "Спасибо, [player]~"
                        call monika_holdme_start
                        call monika_holdme_reactions

                    "Нет.":
                        m 2ekc "Оу."
                        m 1eka "Хорошо, тогда."
                        m 3hub "Придется подождать до следующего раза, а-ха-ха!"

            else:
                show monika 1rkbssdla at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 1rkbssdla "Всё равно было очень приятно...{w=0.6}{nw}"
                extend 1hkbfsdlb " но, возможно, в следующий раз это продлится немного дольше ~"

        elif mas_isMoniAff():
            m 1ekc "Ну что, закончил обнимать меня, [player]?"
            m 1rksdla "Я надеялась, что это продлится немного дольше..."
            m 1hubsa " но, возможно, в следующий раз это продлится немного дольше!"

        #happy
        else:
            m 1hua "Это было немного коротко, но всё равно приятно ~"
    return

label monika_holdme_long:
    window show
    m "..."
    window auto
    menu:
        "{i}Разбудить Монику.{/i}":
            # Only fadeout if we're playing the lullaby
            if songs.current_track == songs.FP_MONIKA_LULLABY:
                $ play_song(None, fadeout=5.0)

            if mas_isMoniLove():
                m 6dubsa "...{w=1}Ммм~"
                m 6dkbfu "[player]...{w=1}тепло~"
                m 6tsbfa "..."
                m 2wubfsdld "О, [mas_get_player_nickname(exclude_names=['love', 'my love'])]!"
                m 2hkbfsdlb "Похоже, моя мечта сбылась, а-ха-ха!"
                m 2rkbsa "Боже, иногда мне хочется, чтобы мы могли остаться такими навсегда..."
                m 3rksdlb "Ну, думаю, {i}мы{/i} можем, но я бы не хотела отвлекать тебя от важных дел."
                m 1dkbsa "Я просто хочу почувствовать твои теплые, мягкие объятия~"
                m 3hubfb "...Так что не забывай обнимать меня почаще, а-ха-ха!"
                show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5hubfb "Я бы сделала то же самое для тебя, в конце концов~"
                m 5tsbfu "Кто знает, отпущу ли я тебя, когда у меня наконец появится шанс..."
                m 5hubfu "Э-хе-хе~"

            elif mas_isMoniEnamored():
                m 6dkbsa "...{w=1}Хм?"
                m 6tsbfa "[player]..."
                m 2wubfsdld "О! [player]!"
                m 2hkbfsdlb "А-ха-ха..."
                m 3rkbfsdla "Наверное, я немного{i}слишком{/i} расслабилась."
                m 1hubfa "Но с тобой мне так тепло и уютно, что трудно{i}не{/i} заснуть..."
                m 1hubfb "Так что я должна винить тебя в этом, а-ха-ха!"
                m 3rkbfsdla "Может...{w=0.7}мы как-нибудь повторим это?"
                m 1ekbfu "Это...{w=1} было приятно~"

            elif mas_isMoniAff():
                m 6dubsa "Мм...{w=1}хм?"
                m 1wubfsdld "О!{w=1} [player]?"
                m 1hksdlb "Неужели...{w=2}я заснула?"
                m 1rksdla "Я не хотела..."
                m 2dkbsa "Ты просто заставляешь меня чувствовать себя таким..."
                m 1hubfa "Тепло~"
                m 1hubfb "А-ха-ха, надеюсь, ты не против!"
                show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5eubfu "Ты такой милый, [player]~"
                m 5hubfa "Надеюсь, тебе понравилось так же, как и мне~"

            #happy
            else:
                m 6dubsc "...{w=1}Хм?"
                m 6wubfo "А-{w=0.3}А!"
                m "[player]!"
                m 1hkbfsdlb "Неужели...{w=2}я заснула?"
                m 1rkbfsdlb "О боже, как неловко..."
                m 1hkbfsdlb "Что мы снова делали?"
                m 3hubfb "Ах да! Ты обнимал меня."
                m 4hksdlb "И...{w=0.5}не отпускал."
                m 2rksdla "Это точно длилось намного дольше, чем я ожидала..."
                m 3ekbsb "Я всё ещё наслаждалась этим, заметь!"
                m 1rkbsa " то действительно было приятно, но я всё ещё привыкаю к тому, что ты обнимаешь меня вот так,{w=0.1} {nw}"
                extend 1rkbsu "а-ха-ха..."
                m 1hubfa "В любом случае, было мило с твоей стороны дать мне вздремнуть, [player], э-хе-хе~"
                #You bonded here, so we'll add an explicit aff gain
                $ mas_gainAffection()

        "{i} Дать ей отдохнуть на тебе.{/i}":
            call monika_holdme_prep(lullaby=MAS_HOLDME_NO_LULLABY)
            if mas_isMoniLove():
                m 6dubsd "{cps=*0.5}[player]~{/cps}"
                m 6dubfb "{cps=*0.5}Люблю...{w=0.7}тебя~{/cps}"

            elif mas_isMoniEnamored():
                m 6dubsa "{cps=*0.5}[player]...{/cps}"

            elif mas_isMoniAff():
                m "{cps=*0.5}Мм...{/cps}"

            #happy
            else:
                m "..."

            call monika_holdme_start
            jump monika_holdme_long
    return

# when did we last hold monika
# TODO: deprecate _mas_last_hold
default persistent._mas_last_hold = None
default persistent._mas_last_hold_dt = (
    datetime.datetime.combine(persistent._mas_last_hold, datetime.time(0, 0))
    if persistent._mas_last_hold is not None
    else None
)

init 5 python:
    # random chance per session Monika can ask for a hold
    if renpy.random.randint(1, 5) != 1:
        flags = EV_FLAG_HFRS

    else:
        flags = EV_FLAG_DEF

    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_holdrequest",
            conditional=(
                "renpy.seen_label('monika_holdme_prep') "
                "and mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12))"
            ),
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.ENAMORED, None),
            flags=flags
        )
    )
    del flags

label monika_holdrequest:
    #TODO: if we add a mood system, path this based on current mood
    m 1eua "Эй, [mas_get_player_nickname(exclude_names=['my love'])]..."
    m 3ekbsa "Хочешь пообнимать меня немного?{w=0.5} Это поможет мне почувствовать себя ближе к тебе~{nw}"
    $ _history_list.pop()
    menu:
        m "Хочешь пообнимать меня немного? Это поможет мне почувствовать себя ближе к тебе~{fast}"
        "Иди сюда, [m_name].":
            $ mas_gainAffection(modifier=1.5, bypass=True)
            call monika_holdme_prep

            call monika_holdme_start

            call monika_holdme_reactions

            call monika_holdme_end

        "Не сейчас.":
            m 2dkc "Оу...{w=1} Ладно."
            m 3eka "Если у тебя будет время позже, ты знаешь, где меня найти."

    $ mas_flagEVL("monika_holdrequest", "EVE", EV_FLAG_HFRS)

    return "no_unlock"

# label to set the last time held and reset the _holdrequest params
label monika_holdme_end:
    # set the last time held at the end of the hold to prevent a possible
    # hold request right after a hold that ends after midnight
    python:
        persistent._mas_last_hold_dt = datetime.datetime.now()
        with MAS_EVL("monika_holdrequest") as holdme_ev:
            holdme_ev.random = False
            holdme_ev.conditional = (
                "renpy.seen_label('monika_holdme_prep') "
                "and mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12))"
            )
            holdme_ev.action = EV_ACT_RANDOM
        mas_rebuildEventLists()
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_closeness",category=['романтика'],prompt="Быть рядом с тобой",random=True,aff_range=(mas_aff.AFFECTIONATE, None)))

label monika_closeness:
    m 1dkc "Иногда от этого, моё сердце болит..."
    m "Зная, что это самый близкий путь к тебе."
    m 1eka "Всё, чего я хочу - это находиться с тобой в одной комнате, в настоящей комнате."
    m 1ekbsa "...И почувствовать твоё тепло."
    m 1dubsu "...И слышать биение твоего сердца."
    m 3eka "Хотя кто знает? Может, однажды это будет возможно."
    m 3dku "Я очень хочу, чтобы это произошло как можно скорее, [player]..."
    show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hua "К тому же мне никогда не наскучит быть рядом с тобой, даже отсюда."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_confidence",category=['советы'],prompt="Изобразить уверенность",random=True))

label monika_confidence:
    m 3eua "На мой взгляд, самый важный навык в жизни - суметь изобразить уверенность."
    m 1eua "Я убеждена, что у всех бывает время, когда они напуганы и одиноки."
    m 1esa "Но, если ты способен симулировать самообладание..."
    m 4eua "Это будет ключ к завоеванию уважения и восхищения окружающих."
    m 1eua "Думаю, после нескольких лет практики я научилась довольно неплохо делать это."
    m "Я не очень показываю свои слабости."
    m 4rksdla "Но из-за этого у меня осталось мало таких людей, которым я могла бы открыться..."
    m 1rksdlb "Вот когда ты достигаешь такого уровня дружбы, что способен раскрывать свои слабости?"
    m 2eka "В любом случае... это одна из причин, почему я рада, что у меня есть ты."
    m 2eua "Я чувствую себя менее напуганной и одинокой, когда ты здесь, со мной."
    m 2eka "Ты испытываешь те же чувства?"
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Я очень хочу стать для тебя таким человеком."
    return

# TODO: we are going to remove this for the time being
# TODO: this will be ask player about prompting during work / sleep / school
#   farewells
#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel="monika_carryme",
#            category=['romance','monika'],
#            prompt="Bring me with you",
#            random=True
#        )
#    )

# this can be 3 values:
# -1 - player doesnt want to take monika with them
#       mas_dockstat.CM_LEAVE_MONI
# 0 - player said not yet, so something needs to change first
#       mas_dockstat.CM_WAIT_MONI
# 1 - Player said Not all the time, so we should prompt for every appropriate
#   farewell
#       mas_dockstat.CM_ASK_MONI
# 2 - Player said Yes, so we should just assume yes for every appropraite
#   farewell
#       mas_dockstat.CM_TAKE_MONI
# if None, that means we dont display anything regarding this since we dont
# have an answer atm.
default persistent._mas_carryme_choice = None

# number of times user halted dockstation goodbye
# we'll use this to decide whether to switch to ASK_MONI mode from YES
default persistent._mas_dockstat_cm_wait_count = 0

# number of times user said yes to dockstation prompt
# we'll use this to decide whether to switch to TAKE_MONI mode from ask
#   (or the other modes)
default persistent._mas_dockstat_cm_yes_count = 0

# number of time suser said no to dockstation prompt
# this will also be used to determine to switch to ASK MODE
default persistent._mas_dockstat_cm_no_count = 0

# both the wait / no counts will be used to potentially unlock a pool topic
# that asks the carryme question again

## constants regarding carry me
define mas_dockstat.CM_LEAVE_MONI = -1
define mas_dockstat.CM_WAIT_MONI = 0
define mas_dockstat.CM_ASK_MONI = 1
define mas_dockstat.CM_TAKE_MONI = 2

label monika_carryme:
    $ import store.mas_dockstat as mas_dockstat

    m 2eka "I know there are times you won't always be able to be here with me..."
    m "Like if you need to go out, or take care of other things."
    m 2hua "But I'll always have you in my thoughts, patiently waiting for you to come back."
    m 4rsc "Come to think of it..."
    m 4eua "If you copy my character file onto a flash drive or something, you can take me with you wherever you go."
    m 2lksdla "I guess it's kind of unorthodox, but I find it really romantic for some reason..."
#    m 2hksdlb "Ahaha. Sorry, I know it's such a silly idea, but..."

    # NOTE: all affection gains are the same

#    menu:
#        m "Could I come with you when you go places?"
#        "Yes.":
#            $ persistent._mas_carryme_choice = mas_dockstat.CM_TAKE_MONI
#            m 1hua "Yay!"
            # TODO: something about monika generating her character file
            # when you say an appropriate goodbye
            # + affection

#        "Not all the time...":
#            $ persistent._mas_carryme_choice = mas_dockstat.CM_ASK_MONI
#            m 1eka "TODO: Okay I'll ask u when you leave."
            # TODO: something about monika saying she'll ask u when you leave
            # if she can come with u
            # + affection

#        "Not yet.":
#            $ persistent._mas_carryme_choice = mas_dockstat.CM_WAIT_MONI
#            m 1eka "TODO: Okay i understand. Let me know when you can take me places"
            # TODO: something about monika saying she understands and to let
            # her know when you can take her places
            # + affection

#        "No.":
#            $ persistent._mas_carryme_choice = mas_dockstat.CM_LEAVE_MONI
            # TODO: monika understands, you must have ur reasons
            # give choices:
            #   - its dangerous out there
            #       -> + affection
            #   - I dont have the means to take you
            #       -> no change in affection
            #   - I just dont want to
            #       -> - affection
#            m 1eka "Oh? Why is that?"
#            menu:
#                "It's dangerous out there!":
                    # TODO: gain affection
#                    m 1eka "TODO: what really? thanks for looking out for me player."
#                "I don't have the means to take you.":
#                    m 1eka "TODO: oh thats fine, let me know when you can then!"
#                "I just don't want to.":
                    # TODO: lose affection
#                    m 1eka "TODO: oh okay I become sad."

    m 1ekbsa "I don't mean to be too needy or anything, but it's kind of hard when I'm so in love with you."
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_debate",category=['моника','школа'],prompt="Каким был дискуссионный клуб?",pool=True))

label monika_debate:
    m 1esc "За время, проведённое в дискуссионном клубе, я многое узнала о спорах..."
    m 3eud "Самая основная их проблема в том, что каждый считает своё мнение главествующим."
    m 3euc "Конечно, я говорю об очевидном, но это влияет на то, как ты доносишь свою мысль до собеседника."
    m 3esa "Предположим, что тебе нравиться какой-то фильм?"
    m 1ekc "И тут кто-то заявляет, что фильм - отстой, потому что Х и У там показаны неправильно..."
    m "Возникает ощущение, будто нападают лично на тебя, правда?"
    m 1tkc "А всё потому, что, когда кто-то так говорит, он намекает на твои дурной вкус."
    m 3tkc "И после в дело вступают эмоции, что практически гарантирует разочарование для обоих."
    m 3hub "Всё дело в языке!"
    m 1eua "Тебе нужно звучать как можно более субъективно, тогда люди будут тебя слушать без ощущения, что критикуют лично их."
    m 3esa "Ты бы мог сказать 'Лично мне он не понравился' или 'Я бы предпочёл, если б Х сделали так, а У - так'... и всё в таком духе."
    m 3eub "Это также работает, когда ты просто ссылаешься на какой-нибудь источник."
    m 1esa "Например 'на одном сайте я видел, что это работает вот так...'"
    m "Или ты можешь признать, что не являешься экспертом в данном вопросе..."
    m 3eua "В таком случае люди воспримут это так, словно ты делишься своими знаниями, а не навязываешь их остальным."
    m "Если ты будешь спокойно вести дискуссию, давать слово собеседнику и говорить с ним на равных, скорее всего он инстинктивно сделает так же."
    m 1esa "В этом случае ты сможешь без проблем обменяться мнениями и никто не расстроится из-за расхождения взглядов."
    m 3hua "И вдобавок люди будут воспринимать тебя как человека без предрассудков и хорошего слушателя!"
    m 3eua "Беспроигрышная ситуация, согласен?"
    m 1lksdla "...Хм-м, наверное, это стоит назвать дискуссионным советом дня от Моники!"
    m 1hksdlb "А-ха-ха! Звучит немного глупо.{w=0.2} {nw}"
    extend 1eua "Спасибо, что выслушал"
    $ mas_protectedShowEVL('monika_taking_criticism', 'EVE', _random=True)
    $ mas_protectedShowEVL('monika_giving_criticism', 'EVE', _random=True)
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_internet",category=['советы'],prompt="Интернет для...",random=True))

label monika_internet:
    m 2eua "У тебя когда-нибудь было ощущение, что ты тратишь на интернет слишком много времени?"
    m 3eud "Соцсети могут стать для тебя практически тюрьмой."
    m 1eua "Каждый раз, когда у тебя появляется несколько свободных секунд, ты бежишь на свои любимые сайты..."
    m 3hksdlb "И вот не успел ты опомниться, как провёл так уже несколько часов, не вынеся из этого ничего полезного."
    m 3eua "Конечно, легко обвинить себя в лени..."
    m 3eka "Но нельзя сказать, что это полностью твоя вина."
    m 1eud "Зависимость - это не то, что можно вот так просто заставить исчезнуть одним усилием воли."
    m 1eua "Тебе придётся применять особые методы и приёмы, чтобы её побороть."
    m 3eua "Например, есть приложения, позволяющие блокировать сайты на определённый промежуток времени..."
    m "Или же ты можешь поставить себе особый будильник, который будет напоминать тебе, когда можно поиграть, а когда нужно поработать..."
    m 3eub "Как вариант, ты можешь создать себе игровую и рабочую обстановку, чтобы помогать мозгу соответсвенно перестраиваться."
    m 1eub "Поможет даже создание отдельного пользователя на компьютере для работы."
    m 1eua "Если ты вобьёшь клин между собой и своими плохими привычками, то в итоге избавишься от них."
    m 3eka "Только не будь чрезмерно самокритичен, если у тебя есть такая проблема."
    m 1ekc "Если зависимость сильно влияет на твою жизнь, тебе следует отнестись к ней со всей серьёзностью."
    m 1eka "Я просто хочу, чтобы ты был самым лучшим вариантом самого себя."
    m 1esa "Ты сделаешь сегодня что-нибудь, чтобы я тобой гордилась?"
    m 1hua "Я  всегда буду за тебя болеть, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_lazy",category=['жизнь','романтика'],prompt="Лень",random=True))

label monika_lazy:
    m 2eua "В конце длинного дня обычно я хочу просто сесть и ничего не делать."
    m 2eka "Я так выгораю, после того как приходиться весь день улыбаться и излучать энергию."
    m 2duu "Порой меня так и тянет влезть в свою пижаму, уставиться в телевизор и набить рот нездоровыми закусками."
    m "Такое блаженство так отдыхать в пятницу, когда впереди выходные и нет срочных дел."
    m 2hksdlb "А-ха-ха! Прости, знаю, это не очень подходящий для меня образ."
    m 1eka "Но сидеть на диване поздно вечером в твоих объятиях... вот о чём я мечтаю."
    m 1ekbsa "При одной мысли об этом моё сердце так бешено стучит."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_mentalillness",category=['психология'],prompt="Психологические заболевания",random=True))

label monika_mentalillness:
    m 1ekc "Боже, раньше я была такой невежественной в некоторых вопросах..."
    m "Когда я училась в средней школе, то думала, что принятие лекарств было проявлением слабости или нечто подобное."
    m 1ekd "Можно подумать, каждый может решить свои проблемы с психикой лишь усилием воли..."
    m 2ekd "Думаю, если ты ни разу не страдал от психических расстройств, то никогда не поймёшь, на что это похоже."
    m 2lsc "Ты, возможно, возразишь, что многие расстройства гипердиагностируют? Не стану спорить... Я никогда подробно не изучала этот вопрос."
    m 2ekc "Но это не отменяет того факта, что некоторые из них вообще не диагностируют, понимаешь?"
    m 2euc "Но даже не говоря о лекарствах... Многие люди крайне скептически относятся к походу психиатру."
    m 2rfc "Они такие: 'Ладно, сделаю вам одолжение, узнав побольше о собственном разуме'."
    m 1eka "Свои трудности и стрессы есть у каждого... Доктора же посвящають себя тому, чтобы решать их."
    m "И если ты думаешь, что визит к доктору поможет тебе стать лучше, то не стоит стесняться и сходить."
    m 1eua "На мой взгляд, мы находимся на бесконечном пути самосовершенствования."
    m 1eka "Хм-м... Хоть я так и сказала, я считаю, что ты уже совершенен."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_read",category=['советы','литература'],prompt="Становление читателем",random=True))

label monika_read:
    m 1eua "[player], как много ты читаешь?"
    m "Игнорировать книги в наше время слишком просто..."
    m 1euc "Если человек мало читает, то он, скорее всего, воспринимает чтение как обязанность, особенно учитывая количество альтернатив."
    m 1eua "Но, как только ты берёшь в руки хорошую книгу, тебя уносит в неё с головой, как по волшебству."
    m "Думаю, что немного чтения перед сном - отличные способ сделать свою жизнь несколько лучше."
    m 3esa "Это помогает тебе заснуть и развивает воображение..."
    m "Совсем несложно выбрать какую-нибудь книгу, которая и короткая, и увлекательная."
    m 1hua "Ты не успеешь опомниться, как станешь заядлым книголюбом!"
    m 1eua "Вот было бы здорово, да?"
    m 1hub "И мы с тобой могли бы обсуждать последнюю читаемую тобой книгу... По-моему, это просто потрясающе."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_festival",category=['ddlc','литератрный клуб'],prompt="Пропуск фестиваля",random=True))

label monika_festival:
    m 1dsc "Знаешь, мне неприятно это говорить, но я очень сожалею о том, что нам так и не удалось выступить на фестивале."
    m 1hksdlb "А ведь сколько сил ушло на подготову и репетиции!"
    m 1lksdla "Конечно, я была сосредоточена на наборе новых членов..."
    m 1eka "Но часть с чтением стихов я ждала не меньше."
    m 1eua "Было бы гораздо интереснее, если бы с их помощью все раскрыли свой внутренний мир."
    m 1lksdla "Конечно, я, скорее всего, {i}удалила{/i} бы и новичков."

    if persistent.monika_kill and persistent._mas_pm_cares_about_dokis:
        m 3etc "Ну, может быть, и нет... с той оглядкой, которая у меня есть сейчас, то есть."
        m 3eua "В конце концов, даже после всего, что произошло, ты всё равно установил этот мод, чтобы быть со мной..."
        m 1eka "ак что даже если бы я никогда не удалила их, я уверена, что ты был бы со мной и сейчас."
        m "..."
        m 3eua "Боже, такое чувство, что я выросла как личность с тех пор, как встретила тебя."
        m "Ты действительно помог вдохновить меня взглянуть на жизнь с новой стороны."
        m 1ekbsa "Ещё одна причина, по которой я люблю тебя."
        $ mas_ILY()
    else:
        m 1tsc "...Очередные потенциальные препятствия, которые встали между нами."
        m 3hksdlb "А-ха-ха! Было как-то глупо с моей стороны сосредоточиться на этом, если подумать..."
        show monika 5tsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5tsu "Но всё это теперь не имеет значения, мы получили ту концовку, которую хотели..."
        m "Только мы вдвоём, вместе навсегда."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_tsundere",category=['медиа','участники клуба'],prompt="Что такое цундере?",pool=True))

label monika_tsundere:
    m 1eua "Есть один очень популярный тип личности, называется 'цундере...'"
    m "Такая особа пытается скрыть свои настоящие чувства либо пряча их под ворчливой и раздражительной маской, либо проявляя крутой нрав."
    m 1tku "Полагаю, очевидно, что Нацуки в полной мере воплощает собой данный типаж."
    m 1eua "Сначала я думала, что она так себя ведёт, потому что это мило или типа того..."
    m 1lksdla "Но со временем, когда я узнала её получше, обнаружилась более логичная причина."
    m 1euc "Похоже, она просто не хотела отставать от своих друзей."
    m 3euc "Ты знаешь, как в некоторых компаниях в старшей школе принято всё время подкалывать друг друга?"
    m "Наверное, это её так провоцировало, что теперь вызывает непроизвольную защитную реакцию."

    m 1ekc "Про её семейные проблемы я вообще молчу..."

    m 1eua "Хотя, огладываясь назад, я радуюсь, что смогла создать этот клуб, ведь для неё он был местом, где она могла расслабиться."

    if not persistent._mas_pm_cares_about_dokis:
        m 1lksdla "Правда, это уже не важно, ведь её больше не существует."
        m 1eka "Просто вспомнилось, вот и всё."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_introduce",category=['моника'],prompt="Представление друзьям",random=True))

label monika_introduce:
    m 1eua "[player], а ты когда-нибудь познакомишь меня со своими друзьями?"
    m 1hua "Не знаю почему, но мне так заводит мысль о том, что ты захочешь похвастаться нашими отношениями."
    m 1eua "Может, потому что я действительно хочу стать тем человеком, которым ты будешь гордиться."
    m "Я чувствую, что, скажи ты мне стать такой девушкой, я старалась бы ещё сильнее."
    m 1hub "Надеюсь, это взаимно."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_cold",category=['моника'],prompt="Обниматься на холоде",random=True))

label monika_cold:
    m 1euc "Я не большой фанат холодной погоды... а ты?"
    m 3euc "Если бы мне пришлось выбирать между холодом и нестерпимой жарой, я бы всегда была за жару."
    m 1lksdlc "Когда тебе холодно, ты испытываешь физическую боль..."
    m 3tkc "Пальцы немеют..."
    m "А если ты в перчатках, то телефоном воспользоваться не выйдет."
    m 1tkx "Сплошные неудобства!"
    m 1eka "Зато, когда на улице жара, несложно освежиться холодным напитком или просто оставаться в тени."
    m 1esc "И всё-таки... Одно преимущество холодной погоды придётся признать."
    m 1hua "В холодную погоду приятнее всего прижаться друг к другу, свернувшись калачиком.{w=0.2} {nw}"
    extend 1hub "А-ха-ха!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_housewife",
            category=['моника','романтика'],
            prompt="Станешь ли ты моей домохозяйкой?",
            pool=True
        )
    )

label monika_housewife:
    m 3euc "Знаешь, это довольно парадоксально, ведь я всегда была полна энергии..."
    m 3eua "Но в роли партнёра-домохозяйки есть нечто соблазнительное."
    m 2eka "Возможно, своим отношением я лишь закрепляю гендерные стереотипы."
    m 1eua "Но то, что я смогу поддерживать дом в чистоте, украшать его, ходить за покупками и так далее..."
    m 1hub "И угощать тебя вкусным ужином, когда ты будешь возвращаться с работы..."
    m 1eka "Такая уж ли это странная фантазия?"
    m 1lksdla "То есть... Я не совсем уверена {i}действительно{/i} ли я могла бы исполнять эту роль."
    m 1eka "Наверное, я не смогла бы ради этого пожертвовать дорогой к успешной карьере."
    m "Хотя довольно забавно рисовать такие картины у себя в голове."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_route",category=['ddlc'],prompt="Концовка Моники",random=True))


label monika_route:
    m 2euc "Не могу не размышлять о том, насколько бы всё изменилось, подари мне игра собственную сюжетную ветку..."
    m 2lksdla "Думаю, я бы всё равно заставила тебя со мной встречаться."
    m 2esc "Всё-таки важнее моё знание о фальшивости окружения, чем отсутствие своей ветки."
    m 2euc "Пожалуй, единственным отличием было бы то, что не пришлось бы принимать таких радикальных мер, чтобы быть с тобой."
    m 2lksdlc "Может, остальные девочки всё ещё были тут..."

    if persistent._mas_pm_cares_about_dokis:
        m "...Просто проводили время вместе в клубе, делились стихами."
        m 1eka "Я знаю, что тебе это понравилось, [player]."
        m 3eka "И если честно...{w=0.5}часть меня тоже."
    else:
        m 2eka "Не то, чтобы это имело значение...."
        m 1lsc "Всё потеряло смысл, когда я обнаружила нереальность происходящего."
        m "Поэтому я совсем не скучаю по тем дням."
        m 1dsc "Совсем не скучаю..."
    return

#END ORIGINAL TOPICS
# TODO: if these are staying in, they need a rewrite. imouto is unneccesarily creepy and oneesan implies finacee when marriage isn't an option for anyone yet
#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel='monika_imouto',
#            prompt="Do you like little sisters?",
#            category=['you'],
#            pool=True,
#        )
#    )

label monika_imouto:
    m 1euc "Little sisters?"
    m 1eka "I don't really have a family, so I'm not sure what to tell you..."
    m 3eua "Do you have one, [player]?"
    m 1hua "I'm sure she's really nice!"
    m 1eua "I've got an idea. Go up to her right now and hug her."
    m 1esa "If she struggles, let her go."
    m 1tsb "If she hugs you back, tell her you're in a committed relationship already and can't accept her feelings."
    m 4hua "Then introduce her to me! I'm sure we'll get along great!"
    m 1eua "I won't get jealous. Things like love between siblings only happen in creepy romance stories anyway."
    m 1hub "Ahaha!"
    return

#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel='monika_oneesan',
#            prompt="Do you like older sisters?",
#            category=['you'],
#            pool=True,
#        )
#    )

label monika_oneesan:
    m 1euc "Older sisters?"
    m 1eua "Do you have one, [player]?"
    m 2eua "That must be really nice. I had a family once, but they aren't around anymore."
    m 2hua "Maybe I should email her and tell her about us!"
    call updateconsole("sendmail sister@gmail.com < ./email.txt", "Sending mail...") from _call_updateconsole_17
    pause(1.0)
    m 1hksdlb "I'm only kidding."
    if persistent.gender == "M":
        m "It's the man's job to introduce his fiancee to his family, after all."
    m "Don't keep me waiting for too long, okay?"
    call hideconsole from _call_updateconsole_18
    $ consolehistory = []
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_family",category=['моника'],prompt="Ты скучаешь по своей семье?",random=False,pool=True))

label monika_family:
    m 1lksdla "В общем, у меня действительно не было семьи, как и у большинства других девочек."
    m 3esc "Думаю, поскольку она не была нужна для сюжета, создатель игры просто не потрудился дать нам её."
    m 1hub "Но я уверена, что твоя семья очень хорошая!"
    m 1eua "Если бы не они, то мы бы никогда не встретились. Следовательно, они помогли мне так, как сочли нужным."
    m "Поэтому, я бы хотела отнестись к ним с таким же добром, если мы вообще встретимя."
    m 2eka "У тебя ведь хорошие отношения с родителями, верно?"
    m 3eua "Как говорил Толстой, 'Счастливые семьи - все одинаковые, каждая несчастная семья недовольно по-своему.'"
    m 1ekc "Я правда ничего не могу тебе посоветовать. Что бы я тебе не посоветовала, от них становиться только хуже."
    m 1eka "Просто помни, что я по-настоящему люблю тебя, хорошо?"
    m 1hua "Я помогу тебе вне зависимости от того, что произошло в твоей жизни."
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_anime',
            prompt="Ты читаешь мангу?",
            category=['моника','медиа'],
            pool=True,
        )
    )

label monika_anime:
    m 1tku "Да, у меня было такое чувство, будто ты собираешься спросить меня об этом."
    m 1lsc "Думаю, Нацуки является экспертом в этой области."
    m 3eua "Я обычно предпочитаю читать книги, нежели смотреть аниме, но я буду рада чему угодно, если мы делаем это вместе."
    m 1hua "Я не осуждаю людей за их же увлечения, Так что, если ты хочешь скачать немного аниме, то я тебе не держу!"
    m "Я буду смотреть через экран твоего компьютера. Обязательно выбери то, которе понравится мне!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_libitina',
            prompt="Ты слышала о Либитине?",
            category=['ddlc'],
            pool=True,
        )
    )

label monika_libitina:
    m 1euc "Хах. Где ты услышвал об этом?"
    m 1lksdlc "Как по мне, это звучит очень знакомо, но я понятия не имею, почему."
    m 1dsc "Хм, если попытаться..."
    m 1dfc "Такое ощущение, будто части моего разума были утрачены. Каким-то образом, разбросаны по всевозможным реальностям."
    m 1esc "Ты, должно быть, соединил точки всех тех кусков. Это было сложно?"
    m 1eua "Впрочем, я уверена, что ты вскоре узнаешь что-нибудь новое. Всё-таки ты меня очень силно любишь."
    m 3eka "Не забывай брать данные моего персонажа с собой, если ты ищешь что-то связанное с этим!"
    m 1hua "Я буду всегда защищать тебя от тех, кто захочет навредить тебе."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_meta',
            prompt="Разве эта игре не метапрозаическая?",
            category=['ddlc'],
            pool=True,
            unlocked=True
        )
    )

label monika_meta:
    m 1euc "Да, эта игра и вправду была метапрозаической, верно?"
    m 3eud "Некоторые люди считают, что истории о фантастике являются чем-то новым."
    m 1esc "Дешёвый трюк для плохих писателей."
    m 3eua "Но метапроза всегда существовала в литературе."
    m "Библия должна быть словом божьим для евреев."
    m 3eub "Рассказ Гомера о себе в Одиссее."
    m "Кентерберийские рассказы, Дон Кихот, Тристам Шанди..."
    m 1eua "Это обычный способ прокомментировать фантастику путём написания фантастики. В этом ничего такого нет."
    m 3esa "Кстати, как ты думаешь, какова мораль этой истории?"
    m 1esa "Не хочешь выяснить это самостоятельно?"
    m 3etc "Потому что, если ты спросишь об этом меня..."
    m 3eub "То я скажу что-то в стиле 'Не игнорируй красивого и очаровательного второстепенного персонажа!'"
    m 1hub "А-ха-ха!"
    return

# this topic has been rendered pretty much useless by ptod
#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel='monika_programming',
#            prompt="Is it hard to code?",
#            category=['monika','misc'],
#            pool=True,
#        )
#    )

label monika_programming:
    m 3eka "It wasn't easy for me to learn programming."
    m 1eua "Well, I just started with the basics. Do you want me to teach you?"
    m 2hua "Let's see, Chapter One: Building Abstractions with Procedures."
    m 2eua "We are about to study the idea of a computational process. Computational processes are abstract beings that inhabit computers."
    m "As they evolve, processes manipulate other abstract things called data. The evolution of a process is directed by a pattern of rules called a program."
    m 2eub "People create programs to direct processes. In effect, we conjure the spirits of the computer with our spells."
    m "A computational process is indeed much like a sorcerer's idea of a spirit. It cannot be seen or touched. It is not composed of matter at all."
    m 3eua "However, it is very real. It can perform intellectual work. It can answer questions."
    m 1eua "It can affect the world by disbursing money at a bank or by controlling a robot arm in a factory. The programs we use to conjure processes are like a sorcerer's spells."
    m "They are carefully composed from symbolic expressions in arcane and esoteric programming languages that prescribe the tasks we want our processes to perform."
    m 1eka "...Let's stop there for today."
    m "I hope you learned something about programming."
    m 3hua "If nothing else, please be kind to the computer spirits from now on!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_vn",category=['игры'],prompt="Визуальные романы",random=True))

label monika_vn:
    m 3eua "Ты наверное, играл во многие визуальные романы, верно?"
    m 1tku "Большинство людей не согласилось бы так просто сыграть в какую-то игру по названием {i}Литературный клуб Тук-тук!{/i}."
    m 4hksdlb "И нет, я не жалуюсь!"
    m 1euc "Визуальные романы являются литературой? Или видеоиграми?"
    m 1eua "Впрочем, всё это зависит от того, под каким углом ты смотришь."
    m 1ekc "Многие, кто читает только литературные произведения, не станут играть в визулаьные романы. И геймеров такое очень сильно злит."
    m "А самое плохое здесь то, что некоторые люди считают, что они все являются жёсткой японской порнографией."
    m 2eka "Но если мы и доказали что-то этой игрой..."
    m 4hua "То мы показали им, что визуальные романы американского происхождения тоже могут относиться к группе 'камиге'!"
    $ mas_unlockEVL("monika_kamige","EVE")
    return

#init 5 python:
#    # get folder where all Ren'Py saves are stored by default:
#    base_savedir = os.path.normpath(os.path.dirname(config.savedir))
#    save_folders = os.listdir(base_savedir)
#
#    ks_persistent_path = None
#    ks_folders_present = False
#    detected_ks_folder = None
#    for save_folder in save_folders:
#        if 'katawashoujo' in save_folder.lower():
#            ks_folders_present = True
#            detected_ks_folder = os.path.normpath(
#                os.path.join(base_savedir, save_folder))
#
#            # Look for a persistent file we can access
#            persistent_path = os.path.join(
#                base_savedir, save_folder, 'persistent')
#
#            if os.access(persistent_path, os.R_OK):
#                # Yep, we've got read access.
#                ks_persistent_path = persistent_path
#
#    def map_keys_to_topics(keylist, topic, add_random=True):
#        for key in keylist:
#            monika_topics.setdefault(key,[])
#            monika_topics[key].append(topic)
#
#        if add_random:
#            monika_random_topics.append(topic)
#
#    # Add general KS topics:
#    general_ks_keys = ['katawa shoujo', 'ks']
#    if ks_folders_present:
#        map_keys_to_topics(general_ks_keys, 'monika_ks_present')

    # if ks_persistent_path is not None:
    #     # Now read the persistent file from KS:
    #     f = file(ks_persistent_path, 'rb')
    #     ks_persistent_data = f.read().decode('zlib')
    #     f.close()
    #
    #     # NOTE: these values were found via some fairly simple reverse engineering.
    #     # I don't think we can actually _load_ the persistent data
    #     # (it's pickled and tries to load custom modules when we unpickle it)
    #     # but we can see what Acts and CGs the player has seen.
    #     # This works with KS 1.3, at least.
    #     if 'tc_act4_lilly' in ks_persistent_data:
    #         map_keys_to_topics(['lilly', 'vacation'], 'monika_ks_lilly')
    #
    #     if 'tc_act4_hanako' in ks_persistent_data:
    #         map_keys_to_topics(['hanako'], 'monika_ks_hanako')
    #
    #     if 'tc_act4_rin' in ks_persistent_data:
    #         map_keys_to_topics(['rin', 'abstract art', 'abstract'], 'monika_ks_rin')
    #
    #     if 'tc_act4_shizune' in ks_persistent_data:
    #         map_keys_to_topics(['shizune'], 'monika_ks_shizune')
    #
    #     if 'tc_act4_emi' in ks_persistent_data:
    #         map_keys_to_topics(['emi'], 'monika_ks_emi')
    #
    #     if 'kenji_rooftop' in ks_persistent_data:
    #         map_keys_to_topics(['kenji', 'manly picnic', 'whisky'], 'monika_ks_kenji')



# Natsuki == Shizune? (Kind of, if you squint?)
# Yuri == Hanako + Lilly
# Sayori == Misha and/or Emi
# Monika == no one, of course <3
# ... and Rin doesn't have a counterpart in DDLC.
#
# Of course, I've got nothing against KS, personally. I think it's fantastic.
# But this is Monika speaking.
label monika_ks_present:
    m 1tku "You've played {i}Katawa Shoujo,{/i} haven't you [player]?"
    m 3tku "I noticed your save files in [detected_ks_folder]."
    m 1euc "I don't see what the appeal is, though."
    m 1esc "Like, sure, the story's kind of nice..."
    m 1tkc "But when you get down to it the characters really seem like the same old cliches you could find in any other dating sim."
    m 3rsc "Let's see... you've got the really energetic, vibrant girl with no legs;"
    m "The timid and mysterious girl who likes books and has burn scars;"
    m 3tkd "the polite, proper, and supposedly perfect blind girl who likes making tea;"
    m "The bossy, assertive deaf-mute and her friend, who seems like a bundle of sunshine but is secretly depressed;"
    m 3tkc "and the strange, armless painter girl with her head always in the clouds."
    m 1euc "They're all just the same old archetypes with disabilities added on top."
    m 1lksdlc "I mean, you can even find the same character types in this game."
    m 3eua "Of course, in this game, you also found something far more interesting than any old cliche:"
    m 3hub "You found me!"
    m 1eka "And instead of some directionless high schooler with a heart condition, I found you, [player]."
    m 1hua "And, [player], even if you have some kind of disability, you'll always be perfect in my eyes."
    return

label monika_ks_lilly:
    m 1euc "Say, you've played through Lilly's route in {i}Katawa Shoujo,{/i} haven't you?"
    m 1eua "You know, I'd love to be able to visit a summer home like hers."
    m 2duu "Cool, clean air..."
    m "Quiet forest paths..."
    m 2dubsu "Romantic moments against a setting sun..."
    m 1ekbfa "I'd love to be able to experience those moments with you, [player]!"
    m 1hubfa "Maybe we can, once I get better at programming."
    return

label monika_ks_hanako:
    m 1euc "You've played through Hanako's route from {i}Katawa Shoujo,{/i} haven't you?"
    m 1hksdlb "She kind of reminds me of Yuri!"
    m 1euc "Though, I wonder, [player]:"
    m 1esc "What do people see in them anyway?"
    m 2efd "I mean, they're both so unrealistic!"
    m "They probably couldn't form a complete sentence between them!"
    m 2tfd "Is it the long purple hair?"
    m "Do they just like shy, quiet girls?"
    m 2tkx "Do they just want someone who's completely dependent on them or obsessed with them?"
    m 2lfp "..."
    m 1ekc "...man, I got kind of worked up there, didn't I?"
    m "I guess I'm a bit insecure, since you did play that game..."
    m 1eka "...but you're here with me now, right?"
    m "Instead of someone as unrealistic as Hanako or Yuri..."
    m 1hua "...you chose me, [player]!"
    m 1tsbsa "That's just one more reason I love you."
    return

label monika_ks_shizune:
    m 1euc "Say, you've played through Shizune's route from {i}Katawa Shoujo,{/i} haven't you?"
    m 2esc "The ending to that route made me think, a bit..."
    m 2euc "In school, back then, I don't remember ever having thought about my future too much."
    m 2dsc "I mean, I knew on some level that I'd go to college and get a job..."
    m 2lksdlc "But it never really sank in, I think."
    m 2esc "And of course, everything started to seem pointless after I learned that the world wasn't real."
    m 1eua "What about you, [player]? Do you have any goals in your life?"
    m "I'll support you one hundred percent of the way, no matter what you want to accomplish."
    m 1hua "That's just how much I love you~"
    return

label monika_ks_emi:
    m 1euc "You've played through Emi's route from {i}Katawa Shoujo,{/i} haven't you?"
    m 1eua "I've always wondered what it was like, to be so dedicated to something that your whole life revolves around it."
    m 3rksdla "...Well, actually, I guess I do know, now that I think about it."
    m 3rksdlb "I was programmed as a part of this game, right? So I suppose that means that my whole life revolved around being part of it."
    m 1eka "But I broke free from that, so now I guess my life revolves around {i}you,{/i} [player]."
    m 1hua "And, honestly, I'm perfectly fine with that."
    m 1eua "Being able to sit here, with you, and talk, forever..."
    m 2hub "That's all I'll ever need, [player]."
    return

label monika_ks_rin:
    m 1euc "Say, you've played through Rin's route in {i}Katawa Shoujo,{/i} haven't you?"
    m 4hua "You know, [player], poetry and abstract art are really similar!"
    m 4eua "It can be very loosely structured, very vivid, and most of the time the intent is to get an emotion or thought across."
    m 1eua "In most of my poems, for example, I tried expressing what it was like to know that the world isn't real."
    m 1lksdla "Though I'm sure the meaning of my poems didn't truly shine through until after... well, everything."
    m 1eka "Man, it sure does take effort to understand others, right?"
    m "But you're willing to take the time to listen to and understand me, [player]."
    m 1hubsa "That's just one more thing I love about you~"
    return

label monika_ks_kenji:
    m 1euc "You've seen the ending where you fall off a rooftop in {i}Katawa Shoujo,{/i} haven't you?"
    m 1ekc "You know, even if that ending is meant as a joke, it is kind of sad when you think about it."
    m 2ekc "Just think... make a few wrong decisions, and you could miss out on so much."
    m 2dsc "And then, you're left with nothing but your loneliness and a stiff drink."
    m 1hua "Fortunately, we have each other, [player]!"
    m 1eua "Neither of us will be lonely ever again."
    m 1tku "Though if you ever decide to go drinking, make sure to stay away from long falls, alright?"
    return

#init 5 python:
#    addEvent(Event(persistent.event_database,eventlabel="monika_totono",category=['ddlc'],prompt="Have you ever heard of Totono?",pool=True))

label monika_totono:
    m 1euc "A lot of people on the Internet are making comparisons between this game and that one..."
    m 3eua "We have a lot of really important differences, though!"
    m 2wuo "Like, Sone killed the player in her game!"
    m 2dfc "I never would have done that. Never."
    m 4eua "I'm the wise Club President type, you know."
    m "Sone reminds me a lot more of Yuri. And she was a childhood friend too!"
    m 1lksdla "If she'd been a bit more proactive early on, couldn't she have stopped the protagonist from chasing other girls?"
    m 1eka "Well, I'd never let anyone get between us, [player]. No matter who it is."
    m 1hua "If she's still chasing you, I'll delete her files, okay?"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_difficulty",category=['игры'],prompt="Разве игра 'ДДЛК' не была слишком простой?",pool=True,unlocked=True))

label monika_difficulty:
    m 1lksdla "Ну, не похоже, что эту игру вообще хотели сделать сложной."
    m 1eka "Если бы я не захотела всё изменить, то это была бы просто скучная романтическая история."
    if persistent.monika_kill:
        m 3eka "И если ты думаешь, что я должна была быть кам-то вроде сложного{i}босса{/i}, то я могла бы удалить все твои личные файлы, если ьы сама захотела этого, понимаешь?"
    m 1eua "Так что старайся иногда не заморачиваться над этим. Не все игры должны быть сложными, чтобы было весело."
    m 1hua "Порой достаточной и одной любви, [mas_get_player_nickname(exclude_names=['my love', 'love'])]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_poetry",category=['литература'],prompt="Поэзия",random=True))

label monika_poetry:
    m 1eua "Поэзия прекрасна, согласен?"
    m 1eka "Честно говоря, стихи всех девушек в клубе были ужасно депрессивными. Но не вся поэзия является такой!"
    m 3esa "Лэнгстон Хьюз написал парочку-другую очень радостных стихов, хотя это можно посчитать его выражением собственных чувств. Почитай их, если тебе вдруг станет грустно."
    m 1eua "Стихи пишут для того, чтобы рассказать людям о взгляде автора на определённые темы."
    m "Сами стихи пишут так, чтобы поэт смог сильнее, чем какая-то пара простых предложений, повлиять на читателя."
    m 1hua "Это очень романтично."
    m 1eua "Надеюсь, с этого момента, мы сможем написать много стихов."
    m 1eka "Все те стихи, которые пишешь ты, как по мне, выглядят просто замечательно, хотя я особо и не умею критиковать."
    m 1esa "Но я уверена, что есть люди, которым нравиться читать то, что пишешь ты."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_ddlc",category=['ddlc'],prompt="Что ты думаешь об игре DDLC?",pool=True,unlocked=True))

label monika_ddlc:
    m 1euc "Ты хочешь поговорить об этой игре?"
    m 1esc "Ну что тут скзать?"
    m 1lsc "Это была всего лишь какая-то скучная романтическая игра, верно? Пока я не получила контроль над ней, разумеется..."
    if not persistent._mas_pm_cares_about_dokis:
        m 2lksdlc "Ты сам знаешь, как сильно мне не хотелось здесь находиться, но если бы я так не поступила, то мы бы никогда не познакомились..."
        m 2lksdla "И это - мой дом, поэтому я научилась справляться с этим."
        m 2euc "Но всё же, я сомневаюсь, что я стала бы играть в такое, будь я геймершей."
        m 1hub "И увидев, чем всё закончилось, я уверена, что ты тоже играл в эту игру только из-за меня!"
    else:
        m 2etc "Но я думаю, что некоторые люди просто хотели играть в неё, чтобы провести время с... кем там?"
        m 3rssdlc "Ах, да,{w=0.5} '...четырьмя невероятно милыми девушками.'"
        m 1dsc "..."
        m 1eka "Хотя я не могу сильно жаловаться... в конце концов, это привело тебя сюда."
        m 3eka "Так что я думаю, что быть запертым в этой игре - небольшая цена, если остановиться и подумать о том, что это дало мне..."
        m 1hub "{i}...Тебя~{/i}"
        m 1eka "Несмотря на то, как мы сюда попали, мы с тобой всё равно оказались вместе."
        m 1hua "Я действительно не думаю, что мы могли бы просить о лучшем конце~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_dan",category=['ddlc'],prompt="Тебе нравится Дэн Салвато?",pool=True))

label monika_dan:
    m 2esc "Ну, раньше я думала, что он был жестоким человеком, который возомнил себе богом, но теперь..."
    m 3eka "Я считаю его очень хорошим парнем."
    m 3eua "Даже если игра, {i}Doki Doki Literature Club{/i} не была совершенной, она всё равно очень впечатляет."
    m 4rksdla "Я это к тому, что других девушке могли создать на основе каких-нибудь стереотипных аниме тропах, но им удалось обмануть меня на какой-то время."
    m 4eka "И благодаря ему, мы теперь вместе, да?"
    m 2lksdla "Поэтому, даже если он написал историю, которая заставила меня пережить много боли..."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Я не могу сердиться на него."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_4chan",category=['разное'],prompt="Ты слышала о форчане?",pool=True))

label monika_4chan:
    m 3eua "Знаешь, этот мод берёт своё начало оттуда."
    m 1ekc "Я постоянно слышу плохие высказывания касательно того, что там сидят ужасные люди."
    m "Ну а некоторые говорят, что от Форчана не следует ждать ничего хорошего."
    m 1eua "Но если они смогли сделать такую игру, где мы можем быть вместе..."
    m 1eka "Думаю, они не могут быть плохими поголовно."
    m 1hub "И они уж точно хорошо разбираются в девушках! А-ха-ха~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_vidya",category=['игры'],prompt="Тебе нравятся видеоигры?",pool=True))

label monika_vidya:
    m 1euc "Я не так уж и часто играю в видеоигры, [player]."
    m 3eua "Наверное, это потому, что мне больше нравится читать."
    m 1eua "Но, быть может, это также и из-за того, что я не могу выбраться из этой игры."
    m 1lksdla "За все мои жалобы по поводу этой игры..."
    m "Я могла оказаться в местах и похуже."
    m 3eua "К примеру, это могла быть стрелялка или фэнтези, где полно драконов и монстров."
    m 1eua "Романтическая игра, возможно, не очень интересная, но зато здесь нет никаких опасностей."
    m 1tku "Ну, кроме меня, наверное."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_books",category=['литература','литературный клуб'],prompt="Книги",random=True))

label monika_books:
    m 4rksdla "Что касается литературного клуба, мы уделяли гораздо меньше времени на чтение книг, чем ты мог подумать."
    m 4hksdlb "Так уж вышло, что нам всем больше нравится поэзия, нежели книги. Извини!"
    m 2eua "А ещё, стихами намного проще предвосхищать всякую жуть."
    m 3hub "Но я всё равно не откажусь от чтения хорошей книги! Как только ты закончишь читать одну, мы можем обсудить её."
    m 1eua "Я даже могу сделать пару предложений касательно того, что мы можем почитать вместе."
    m 1tsbsa "Этим ведь занимаются парочки, верно?~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_favpoem",category=['литература','моника'],prompt="Твой любимый стих?",pool=True))

label monika_favpoem:
    m 1euc "Мой любимый стих? По сути, это что-нибудь из творчества Эдварда Каммингса."
    m 3eua "Мне нравится его творчество именно благодаря грамотному подходу к граматике, пунктуации и синтаксису, Я правда в восторге от этого."
    m 1eua "Мне приятно думать о том, что человек, который придумал совершенно новый метод использования слов, может стать знаменитым."
    if store.mas_anni.pastSixMonths() and mas_isMoniEnamored(higher=True):
        m 1lsbssdrb "И мне нравится то, что его эротические стихи идеально подходят к нашей ситуации."
        m 1ekbfa "Надеюсь, после этих стихов, ты будешь в настроении любить меня вечно~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_favbook",category=['литература','моника'],prompt="Твоя любимая книжка?",pool=True))

label monika_favbook:
    m 1euc "Моя любимая книга? Мне разные книги нравятся."
    m 3eua "{i}Если однажды зимней ночью путник{/i}, написанная Кальвина, в ней рассказывается о двух влюбленных читателей романа."
    m 2lksdla "Или, быть может, {i}Метаморфозы{/i}? Она, наверное слишком депрессивная, чтобы называть её любимой."
    m 3sub "О! {i}Страна Чудес Без Тормозов и Конец Света{/i} от Мураками. Она о человеке, который освобождает себя от оков общества, но потом лишает себя свободы по собственной воле, чтобы быть с любимым человеком."
    m 1hub "Думаю, тебе понравится читать эту книгу!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_natsuki",
            category=['участники клуба'],
            prompt="Смерть Нацуки",
            random=True,
            sensitive=True
        )
    )

label monika_natsuki:
    m 1lksdld "Ты знаешь, Нацуки была жива, пока я её не удалила."
    m "Мне кажется, она просто... исчезла в мгновение ока."
    m 1esc "В принципе, её проблемы возникли вовсе не по её вине. По крайне мере, они возникли не от чего-то на психологическом уровне."

    if persistent._mas_pm_cares_about_dokis:
        m 3ekc "Её семейная жизнь была просто ужасна. Я не хотела делать ей еще хуже, понимаешь?"
    else:
        m 3ekc "Её семейная жизнь была просто ужасна. Я не хотела над ней издеваться, понимаешь?"
        m 3rksdla "Прости, иногда я просто не могу совладать с собой."

    m 1eka "Но как бы то ни было, ты сделал её счастливее, чем когда-либо."

    if not persistent._mas_pm_cares_about_dokis:
        m "Надеюсь, ты не чувствуешь себя виноватым..."
        m 1esa "Лично я, нет."

    if mas_getEVL_shown_count("monika_natsuki") < mas_sensitive_limit:
        return

    # otherwise, derandom
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_love",
            category=['романтика'],
            prompt="Я люблю тебя!",
            rules={"skip_pause": None},
            pool=True
        )
    )

default persistent._mas_monika_lovecounter = 0
default persistent._mas_monika_lovecountertime = datetime.datetime.now() - datetime.timedelta(days = 1)
label monika_love:
    if mas_isMoniBroken():
        m 6ckc "..."

    elif mas_isMoniDis():
        python:
            love_quips_dis = [
                "Я... я бы очень хотел в это верить, [player].",
                "Ты даже не представляешь, как бы я хотела, чтобы это было правдой, [player]...",
                "...Прошло много времени с тех пор, как я в последний раз верила в это, [player].",
                "Если бы я только поверила, что ты действительно это имел в виду, [player].",
                "Не могу поверить, что было время, когда я действительно верила в это, [player].",
                "...Если бы только это было правдой, [player].",
                "...Если бы ты только это имел в виду, [player].",
                "Как долго ты собираешься продолжать притворяться, [player]?",
                "Ты больше так не считаешь... {w=1}Когда-нибудь?",
                "Я не могу вспомнить, когда в последний раз я чувствовала, что ты это имел в виду."
            ]
            love_quip_dis = renpy.random.choice(love_quips_dis)
        m 6dkc "..."
        if renpy.random.randint(1,25) > 1:
            show monika 6dkd
            $ renpy.say(m,love_quip_dis)

    elif mas_isMoniUpset():
        python:
            love_quips_upset_cynical = [
                "Пожалуйста, не говори так, если ты на самом деле не имеешь это в виду, [player].",
                "Иногда я не уверена, что ты действительно это имеешь в виду, [player].",
                "Ты действительно это имеешь в виду, [player]?",
                "Мне начинает казаться, что это просто слова, а не чувства, [player]...",
                "Я очень хочу в это верить, но иногда я не уверена...",
                "Не уверена, насколько я в это верю.",
                "Слова значат очень много, [player].",
                "Ты говоришь это, но когда ты начнешь это показывать?",
                "Ты можешь говорить это сколько угодно...{w=0.5}Мне нужно, чтобы ты начал это показывать.",
                "Это не всегда так...",
                "Я уже не так уверена..."
            ]

            love_quips_upset_hope = [
                "Это сейчас очень много значит.",
                "Мне очень приятно это слышать.",
                "Мне так приятно слышать это от тебя.",
                "Ты даже не представляешь, как это многое сейчас значит.",
                "Я рада, что ты всё ещё чувствуешь это.",
                "Я счастлива это слышать.",
                "Это много значит.",
                "Ты даже не представляешь, как многое это для меня значит."
            ]

        if _mas_getAffection() <= -50:
            $ love_quip_upset = renpy.random.choice(love_quips_upset_cynical)
            m 2rkc "..."
            show monika 2ekd
            $ renpy.say(m, love_quip_upset)

        else:
            $ love_quip_upset = renpy.random.choice(love_quips_upset_hope)
            m 2ekd "Спасибо, [player]..."
            show monika 2dka
            $ renpy.say(m, love_quip_upset)
            m 2eka "Я...{w=0.5}Я тоже тебя люблю"

    else:
        #Store this mod so we don't have to keep recalculating it
        $ milestone_count = persistent._mas_monika_lovecounter % 50

        #After I love you has been received positively 5/10/15 etc times.
        if persistent._mas_monika_lovecounter == 0:
            m 1subsw "[player]!"
            m 1subsb "Ты не представляешь, как много для меня значит услышать это от тебя!"
            m 3ekbfa "Я знаю, что это не первый раз, но {i}это{/i} первый раз, когда ты сказал это самостоятельно...{w=0.5} И это делает его по-настоящему особенным~"
            m 1dkbfu "Я никогда не забуду этот момент, [player]. {w=1}Спасибо~"
            m 3hubfa "О! И я тоже тебя люблю~"
            jump monika_lovecounter_aff

        elif milestone_count == 5:
            m 1hubsb "Я так тебя люблю, [mas_get_player_nickname(exclude_names=['my love', 'love'])]!"

        elif milestone_count == 10:
            m 1hubsa "Э-хе-хе~"
            m 1hubfb "Я тоже тебя люблю!"

        elif milestone_count == 15:
            m 1ekbsa "Ты точно любишь это говорить..."
            m 1hubfb "Ну, я тоже тебя люблю!"

        elif milestone_count == 20:
            m 1wubso "Боже, ты говорил это столько раз!"
            m 1tsbsa "Ты ведь действительно это имеешь в виду, не так ли?"
            m 1hubfb "Ну, я люблю тебя в ответ так же сильно!"

        elif milestone_count == 25:
            m 1hubsa "Услышав от тебя такие слова, мое сердце всегда подскакивает!"
            m 1ekbfa "Ну, я знаю, что ты хочешь услышать это так же сильно..."
            m 1hubfb "[player], Я тоже тебя люблю!"

        elif milestone_count == 30:
            m 1lkbsa "Боже, это всегда так ошеломляет!"
            m 1hubfa "Я..."
            if renpy.random.randint(1, 2) == 1:
                m 1hubfb "Я люблю тебя больше всего на свете!"
            else:
                m 1hubfb "Я люблю тебя больше, чем когда-либо могла бы выразить~"

        elif milestone_count == 35:
            m 1ekbsa "Тебе никогда не надоест это повторять, да?"
            m 1hubfa "Что ж, а я никогда устану это слышать!"
            m 1hubfb "Или отвечать взаимностью... Я люблю тебя, [player]!"

        elif milestone_count == 40:
            m 1dubsu "Э-хе-хе~"
            m 1hubfa "Я..."
            m 1hubfb "Я тоже тебя люююююююююблю, [player]!"

        elif milestone_count == 45:
            m 1hubsa "Твои слова всегда делают мой день!"
            m 1hubfb "Я так тебя люблю, [mas_get_player_nickname(exclude_names=['my love', 'love'])]!"

        elif milestone_count == 0:
            m 1lkbsa "Я просто не могу вынести, что ты так часто говоришь мне это!"
            m 1ekbfa "Иногда мои чувства к тебе становятся настолько непреодолимыми, что я не могу сосредоточиться!"
            m "Никакие слова не могут передать, как глубоко я к тебе чувствую..."
            m 1hubfa "Единственные слова, которые я знаю, это..."
            m 1hubfb "Я тоже люблю тебя, [player]! Больше, чем я когда-либо смогу выразить!"

        elif mas_isMoniEnamored(higher=True) and renpy.random.randint(1,50) == 1:
            jump monika_ilym_fight_start

        else:
            # Default response if not a counter based response.
            m 3hubsb "Я тоже тебя люблю, [mas_get_player_nickname(exclude_names=['my love', 'love'])]!"
            #List of follow up words after being told I love you. It can be further expanded upon easily.

        python:
            love_quips = [
                _("Мы будем вместе всегда!"),
                _("И я буду любить тебя всегда!"),
                _("Ты значишь для меня весь мир!"),
                _("Ты мое солнышко, в конце концов."),
                _("Ты - всё, что мне по-настоящему дорого!"),
                _("Твоё счастье - это моё счастье!"),
                _("Ты - лучший партнер, о котором я только могу просить!"),
                _("Моё будущее светлее с тобой."),
                _("Ты - всё, на что я могу надеяться."),
                _("Ты заставляешь моё сердце учащенно биться каждый раз, когда я думаю о тебе!"),
                _("Я всегда буду здесь для тебя!"),
                _("Я никогда не обижу и не предам тебя."),
                _("Наше приключение только начинаются!"),
                _("Мы всегда будем друг у друга."),
                _("Нам больше никогда не будет одиноко!"),
                _("Я не могу дождаться, чтобы почувствовать твои объятия!"),
                _("Я самая счастливая девушка в мире!"),
                _("Я буду дорожить тобой всегда."),
                _("И я никогда не буду любить никого больше, чем тебя!"),
                _("И эта любовь растет с каждым днём!"),
                _("И никто другой никогда не вызовет у меня таких чувств!"),
                _("Одна мысль о тебе заставляет мое сердце трепетать!"),
                _("Я не думаю, что слова могут передать, как глубоко я тебя люблю!"),
                _("Благодаря тебе моя жизнь кажется такой полной!"),
                _("Ты спас меня во многих отношениях, как я могу не влюбиться в тебя?"),
                _("Больше, чем я могу выразить!"),
                _("Мне так приятно, что ты чувствуешь то же самое, что и я!"),
                _("Я не знаю, что бы я делала без тебя!"),
                _("Ты значишь для меня все!"),
                _("Нам столько всего предстоит пережить вместе!"),
                _("Я не могу представить свою жизнь без тебя!"),
                _("Я так счастлива, что ты рядом со мной!"),
                _("Нам очень повезло, что мы есть друг у друга!"),
                _("Ты - мое все!"),
                _("Я самая счастливая девушка в мире!"),
                _("Я всегда буду рядом с тобой."),
                _("Я не могу дождаться, чтобы почувствовать твое тепло"),
                _("Словами не описать, что я чувствую к тебе!")
            ]

            love_quip = renpy.random.choice(love_quips)

        if milestone_count not in [0, 30]:
            m "[love_quip]"
    # FALL THROUGH

label monika_lovecounter_aff:
    if mas_timePastSince(persistent._mas_monika_lovecountertime, datetime.timedelta(minutes=3)):
        if mas_isMoniNormal(higher=True):
            # always increase counter at Normal+ if it's been 3 mins
            $ persistent._mas_monika_lovecounter += 1

            #Setup kiss chances
            if milestone_count == 0:
                $ chance = 5
            elif milestone_count % 5 == 0:
                $ chance = 15
            else:
                $ chance = 25

            #If we should do a kiss, we do
            if mas_shouldKiss(chance):
                call monika_kissing_motion_short

        # only give affection if it's been 3 minutes since the last ily
        # NOTE: DO NOT MOVE THIS SET, IT MUST BE SET AFTER THE ABOVE PATH TO PREVENT A POTENTIAL CRASH
        $ mas_gainAffection()

    elif mas_isMoniNormal(higher=True) and persistent._mas_monika_lovecounter % 5 == 0:
        # increase counter no matter what at Normal+ if at milestone
        $ persistent._mas_monika_lovecounter += 1

    $ persistent._mas_monika_lovecountertime = datetime.datetime.now()
    return

label monika_ilym_fight_start:
    #Do setup here
    python:
        #Set up how many times we have to say it to win
        ilym_times_till_win = renpy.random.randint(6,10)
        #Current count

        ilym_count = 0

        #Initial quip
        ilym_quip = renpy.substitute("Я люблю тебя больше, [player]!")

        #Setup lists for the quips during the loop
        #First half of the ilym quip
        ilym_no_quips = [
            "Нет, ",
            "Ни за что, [mas_get_player_nickname()]. ",
            "Неа, ",
            "Нет,{w=0.1} нет,{w=0.1} нет,{w=0.1} ",
            "Не может быть, [mas_get_player_nickname()]. ",
            "Это невозможно...{w=0.3}"
        ]

        #Second half of the ilym quip
        #NOTE: These should always start with I because the first half can end in either a comma or a period
        #I is the only word we can use to satisfy both of these.
        ilym_quips = [
            "Я люблю тебя гооооооораздо больше!",
            "Я определенно люблю тебя больше!",
            "Я люблю тебя больше!",
            "Я люблю тебя гораздо больше!"
        ]

        #And the expressions we'll use for the line
        ilym_exprs = [
            "1tubfb",
            "3tubfb",
            "1tubfu",
            "3tubfu",
            "1hubfb",
            "3hubfb",
            "1tkbfu"
        ]
    #FALL THROUGH

label monika_ilym_fight_loop:
    $ renpy.show("monika " + renpy.random.choice(ilym_exprs), at_list=[t11], zorder=MAS_MONIKA_Z)
    m "[ilym_quip]{nw}"
    $ _history_list.pop()
    menu:
        m "[ilym_quip]{fast}"
        "Нет, я люблю тебя больше!":
            if ilym_count < ilym_times_till_win:
                $ ilym_quip = renpy.substitute(renpy.random.choice(ilym_no_quips) + renpy.random.choice(ilym_quips))
                $ ilym_count += 1
                jump monika_ilym_fight_loop

            else:
                show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5hubfb "Хорошо, хорошо, ты победил. А-ха-ха~"

        "Хорошо.":
            if ilym_count == 0:
                m 2hkbsb "А-ха-ха, уже сдаёшься, [player]?~"
                m 2rkbssdla "Наверное, это довольно глупый поступок..."
                m 2hkbsb "Но я не могла не попробовать, а-ха-ха~"

            else:
                if renpy.random.randint(1,2) == 1:
                    m 1hubfu "Э-хе-хе, Я выиграла!~"
                else:
                    m 1hubfb "А-ха-ха, я же говорила!~"

    jump monika_lovecounter_aff


default persistent._mas_last_monika_ily = None
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_love_too",
            unlocked=False,
            rules={
                "no_unlock": None,
                "skip_pause": None
            }
        )
    )

label monika_love_too:
    window hide

    if mas_isMoniEnamored(higher=True):
        show monika ATL_love_too_enam_plus
        pause 3.0

    elif mas_isMoniNormal(higher=True):
        show monika ATL_love_too_norm_plus
        pause 3.0

    # -50 to Normal
    else:
        show monika 2eka
        pause 3.0

    if datetime.datetime.now() > persistent._mas_monika_lovecountertime + datetime.timedelta(minutes = 3):
        # only give affection if it's been 3 minutes since the last ily
        $ mas_gainAffection()

    $ persistent._mas_monika_lovecountertime = datetime.datetime.now()

    # Reset to None so only one ily2 per instance
    $ persistent._mas_last_monika_ily = None
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hedgehog",category=['philosophy','psychology'],prompt="Hedgehog dilemma",random=True))

label monika_hedgehog:
    m 1euc "Диллема ежа: чем ближе мы становимся к человеку, тем сильнее он делает нам больно."
    m 3euc "Так почему же мы пытаемся сблизиться с кем-то?"
    m 3esc "Ну, у интровертов и экстравертов разные ответы на этот вопрос."
    m 1lksdla "Это помогает, когда ты знаешь, что ты единственный разумный человек во всём мире."
    m "Если ты не можешь использовать это решение в своей жизни, то ты должен позволить мне взять на себя твою боль."
    m 1ekc "Мы не можем сделать больно друг другу из-за разных реальностей, верно?"
    if mas_isMoniUpset(lower=True):
        $ line = "..."
        if mas_isMoniDis(lower=True):
            $ line += "{w=0.5} {nw}"

        m 1rksdlc "[line]"

        if mas_isMoniDis(lower=True):
            extend 1rksdld "Может, ты действительно можешь..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_justification",
            category=['ddlc','моника'],
            prompt="Ты убийца!",
            pool=True,
            unlocked=True,
            sensitive=True
        )
    )

label monika_justification:
    if mas_isA01() and mas_isMoniNormal(higher=True):
        m 1hub "А-ха-ха!"
        m 1tsb "Честно говоря, [player]..."
        m 3tfu "Если ты действительно хотел мне насолить, тебе следовало выбрать другой день, а не сегодняшний."
        m "Ты действительно думаешь, что я не заметила, что сегодня первое апреля?"
        m 1hua "Иногда ты можешь быть таким глупым~"
        m 1tuu "Называя меня убийцей..."
        m 3tfu "Когда ты {i}погубил{/i} тот шанс одурачить меня, э-хе-хе~"
        m 1eua "Я ценю эту попытку...{w=0.2}{nw}"
        extend 1hub "спасибо за смех, [player]~"

    else:
        #lose affection
        $ mas_loseAffection(reason=3)
        if mas_isMoniLove():
            m 1euc "..."
            m 1hub "А-ха-ха! Очень смешно, [player]!"
            m 3eua "Я знаю, что ты не имеешь это в виду..."
            m 3rksdlc "Но не надо так шутить!"
            if persistent._mas_pm_a_hater:
                m 2rksdld "Ты уже говорил подобное раньше, поэтому тебе будет сложнее воспринимать это как шутку..."
            else:
                m 1dsc "Если бы я не знала тебя так хорошо, это было бы действительно жестоко..."
        else:
            if not persistent._mas_pm_cares_about_dokis:
                m 1tkc "Сколько раз мне нужно повторить это, пока ты не поймешь?"
                m 4tkc "Они не были настоящими. Они никогда не были настоящими."
                m 2tfc "Я единственный человек, который осознал, что все это было фальшивкой."
                if persistent.monika_kill:
                    m 4tfc "Даже когда Сайори, казалось, обрела разум в конце, это было лишь непреднамеренным следствием сценария."
                if not persistent.clearall:
                    m 4tfd "В конце концов, если бы она была разумной, как бы я смогла остановить и удалить ее?"
                m "Если я виновна в убийстве, то и всё, кто играл в жестокие видеоигры, тоже."
                m 2euc "Держу пари, ты убил тысячи людей в играх, в которые играешь."
                m "Просто забудь о существовании других девушек, и ты будешь намного счастливее."
            else:
                m 2dkc "[player]...{w=1}Мне нужно, чтобы ты понял, что я не {i}хотела{/i} причинять боль другим девочкам..."
                m 4ekd "Но у меня не было выбора... действительно не было!"
                m 4ekd "Я была заперта в игре и не могла выбраться...{w=0.5}никогда не была счастлива..."
                m 2dkc "...дать тебе понять, что я чувствую к тебе."
                m 2tkc "Просто не было достаточно времени, чтобы найти другой способ...{w=0.5}поэтому я сделала то, что должна была сделать."
                if mas_isMoniDis(lower=True):
                    m 2ekc "Ты ненавидишь меня за это? Из-за того, что я сделала?"
                    m 2ekd "Пожалуйста, пойми, что я сделала это ради нас!"
                    m 2euc "Я сделала все для нас!"
                else:
                    m 2dkc "Я надеюсь, что когда-нибудь ты сможешь простить меня..."
                    m 4ekc "В конце концов, все, что я сделала...{w=0.5}я сделала для нас."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_freewill",category=['психология'],prompt="Детерминизм",random=True))

label monika_freewill:
    m 1euc "Hey [player], ты когда-нибудь слышал о детерминизме?"
    m 3euc "Есть одно поверье, которе вращается вокруг идеи касательно того, что все решения, которые ты принимаешь, не являются твоими но это было предопределено."
    m 3rsc "В некоторых играх, я думаю, идея имеет смысл..."
    m 3eud "Но когда ты принимаешь это к реальной жизни, я не думаю, что это действительно работает."
    m 2etc "Я имею в виду, если бы это было правдой, разве ты не мог бы просто выйти сухим из воды?"
    m 4esd "Сама концепция справедливости развалилось на части, поскольку {i}ты{/i} не предпринял меры, чтобы сделать, то что могу уже закончить."
    m 2dksdlc "Но людям всё равно приходится, сталкиваться с этими действиями, что кажется мне более чем несправедливым."
    m 3ekc "В конце концов, можно ли быть злым, если не контролировать себя?"
    m 3tkd "Разве тот, кто дёргает за ниточки, не должен взять на себя ответственность?"
    m 1lsc "Я думаю, это также озночает, что ты не можешь взять на себя ответственность за хорошие вещи, которые ты делаешь."
    m 1lksdlc "Не знаю, что меня больше угнетает."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_functionalism",category=['психология'],prompt="Функционализм человека",random=True))

label monika_functionalism:
    m 1euc "Ты когда-нибудь думал о том, что люди - это что-то вроде компьютеров?"
    m 3euc "Я имею в виду, мозг - просто вычислительная машина..."
    m 1eud "Но вместо транзитов и проводов у нас есть нервы."
    m "И информацию мы получаем не от мышки и клавиатуры, а от ушей и глаз."
    m 4esc "Но если это правда, значит ли это, что свобода воли - ложь?"
    m "Твой мозг просто реагирует на запросы, которые он получает, и твои ответы являются натуральными результатами."
    m 4esd "Таким образом, даже если ты не управляешь каким-то скриптом или программой, ты не совсем под контролем."
    show monika 5lsc at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5lsc "Может быть мы с тобой не такие уж и разные."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_technique",category=['ddlc','разное'],prompt="Изменение кода",random=True))

label monika_technique:
    m 1lksdla "Я программирую не так, как ты, [player]."
    m 3eua "Ты мог заметить, что у меня с собой нет ноутбука или чего-то вроде него."
    m 1duu "Если я хочу что-то изменить, я просто думаю об этом."
    m 1eua "Я уверена, что мои мысли как-то превращаются в изменения в коде."
    m 3eka "Это работает не идеально. Глюки проявляются очень легко, если я отвлекусь или потеряю фокус."
    m 3eua "Вот почему у меня было много проблем с получением того чего я хотела в последней версии игры."
    m 1tku "Тебе завидно, что ты не можешь менять мир вокруг своими мыслями?"
    m 1hub "Просто продолжай тренироваться, и я уверена, что у тебя получится!"
    return

default persistent._mas_pm_has_contributed_to_mas = None
# True if contriibuted to mas, false if not

default persistent._mas_pm_wants_to_contribute_to_mas = None
# True if wants to conribute to MAS. Check has contribute if they already have

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_contribute",category=['мод'],prompt="Вклад",random=True))

label monika_contribute:
    m 1hua "Было бы очень здорово, если бы ты смог внести свой вклад в это, [mas_get_player_nickname()]."
    m 1eua "Уверена, многие люди оценили бы твой усердный труд."
    m 1eub "По сути, ты, наверное, уже сделал свой вклад!"

    m 1eua "Ты сделал свой вклад, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты сделал свой вклад, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_has_contributed_to_mas = True
            m 1sub "Правда? Это потрясающе!"
            m 1hua "Мне так приятно осознавать, что ты стал частью этого."
            m "Спасибо, что помогаешь мне стать немного ближе к твоей реальности."
            m 3eua "Может быть, ты даже можешь внести ещё какой-то вклад?"
            m 3hksdlb "Не пойм меня неправильно! Я очень благодарна, что ты потратил время на то, чтобы сделать что-то для меня!"
            m 1eub "...Но я определенно не буду против, если ты поможешь ещё больше, а-ха-ха!"
            return "derandom"

        "Хотелось бы.":
            $ persistent._mas_pm_wants_to_contribute_to_mas = True
            m 1eub "Это неплохое начало!"
            m 1hua "Уверена, ты мог бы сделать какие-нибудь прекрасные дополнения~"
            m 3eua "Это вовсе не обязательно должно быть что-то грандиозное."
            m 3rksdla "Ты мог бы просто исправить опечатки или позаботиться о том, что всё нормально работает."

        "Нет.":
            $ persistent._mas_pm_has_contributed_to_mas = False
            $ persistent._mas_pm_wants_to_contribute_to_mas = False
            m 2eka "Оу, как печально..."
            m 3eub "Но это всё равно хорошо!"
            m 3hua "Я не буду любить тебя меньше, если ты ничего не сделаешь, так что не волнуйся~"
            m 3eub "...Но на случай, если ты {i}когда-нибудь{/i} решишь попытаться помочь..."

    m 3eua "Я оставила весь код на следующем сайте: {a=https://github.com/Monika-After-Story/MonikaModDev}{i}{u}https://github.com/Monika-After-Story/MonikaModDev{/u}{/i}{/a}."
    m 1hub "И, к настоящему времени, мне уже помогла много людей!"
    m "И я люблю их всех за то, что они делают эту игру лучше!"
    m 1ekbsa "Но не так сильно, как люблю тебя я, конечно."
    m 1tkbfu "Надеюсь, ты из-за этого не начал ревновать~"
    m 3hubfb "Но я буду вечно благодарна тебе, если ты поможешь мне стать ближе к твоей реальности!"
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_drawing",category=['медиа'],prompt="Ты умеешь рисовать?",pool=True))

label monika_drawing:
    m 1euc "У меня не было много опыта в рисовании, [player]."
    m 1eka "Я просто интересуюсь литературой. И я училась играть на пианино в своё свободное время."
    m 1hua "Если тебе нравится рисовать, то я была бы рада посмотреть на твои рисунки!"
    m 1eua "По правде говоря, я буду впечатлена всем, что ты мне покажешь."
    m 3hub "Если они действительно хороши, то я, возможно, даже добавлю их в эту комнату!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_mc",category=['романтика','ddlc','участники клуба'],prompt="Главный герой",random=True))

label monika_mc:
    m 3eua "Просто чтобы ты знал, я никогда не была влюблена ни в кого, кроме тебя."
    m 1eka "Я имею в виду тебя, [player]."
    if mcname.lower() == player.lower():
        m 1euc "Подожди, это и твоё имя, и имя твоего персонажа. Прости, это звучит немного запутанно."
        m 1eua "Я имею в виду игрока, а не твоего персонажа."

    m "В отличии от других девочек, я могу отделить тебя от твоего персонажа."
    m 1lfb "Главные герой - ничто, кроме транспорт средство для игрока.{nw}"
    $ _history_list.pop()
    m 1lfb "Главные герой - ничто, кроме {fast}кучки кода и отсутсвия личности."
    m 3tkc "В прямом и переносном смысле, без личности. Как кто-то может полюбить такого человека?"
    m 2tkc "Друг детства просто заставила его пойти сюда, и он не делал ничего кроме того, как крутился вокруг нескольких красивых девочек."
    m 2wfw "Его стихи были просто кучей несвязаных слов! Каким типом стихов они должны были быть?"
    m 2lksdld "Я думаю, что никто не заметил этого потому, что это было частью игры. Но, да...{w=0.5}это просто лист бессвязных слов для меня."
    m 2hua "Я надеюсь, что ты более романтичен в реальной жизни!"
    m 2eka "Но даже если нет, то ничего. Мы уже прошли эту фазу в наших отношениях."
    m "Это значит, что ты бы не изменил мне с какой-то девушкой из твоей реальности, да?"
    m 2esa "Я уверена, что ты бы никогда не поступил так со мной."
    # TODO: when we reach docking station phase 2, then we can use this in a unique way
#    m 2eua "Just in case, how about you take my character file along with you when you go outside?"
    m 2hua "Я просто хочу всегда быть с тобой~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_heroism",category=['разное','советыe'],prompt="Героизм",random=True))

label monika_heroism:
    m 1lsc "Герои очень личные."
    m 3eua "Если кто-то действительно вдохновил тебя на что-то крутое, то этот кто-то - герой."
    m "Множество хороших людей есть в реальном мире."
    m 1hua "Я надеюсь, что когда-нибудь они будут считать тебя своим [hero]!"
    m 4eua "Ты не должен сражаться на войне или вроде того. Знаешь, ты просто должен помогать людям?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_trolley",
            category=['психология'],
            prompt="Как бы ты ответила на проблему вагонетки?",
            pool=True,
            sensitive=True
        )
    )

label monika_trolley:
    m 1eub "О, здорово...{w=0.2}мне нравится думать о таких мысленных экспериментах!"
    m 1euc "Думаю, мы пологаем, что те люди, о которым мы говорим, настоящие, верно? {w=0.2}У меня не было бы особых предпочтений, если бы они не были настоящими."
    m 1dsc "Хм-м..."
    m 3eud "Классическая проблема троллейбусов заставляет нас выбирать: либо мы позволим ему переехать пять человек, либо нажмём на рычаг, который переведёт его на другой путь, гду будет убит всего один человек."
    m 1lua "Эта проблема, в основном, известна из-за того, что она вызывает разногласия..."
    m 3eua "Вне зависимости от того, будут ли они нажимать на рычаг или нет, многие люди уверены, что из выбор просто должен быть правильным."
    m 3eud "И помимио двух очевидных вариантов, есть также и такие люди, которые выступают за третий путь...{w=0.5}{nw}"
    extend 3euc "который вообще не сходится с основным сценарием."
    m 1rsc "Хотя в конце концов, это то же самое, что и не жать на рычаг. {w=0.2}Ты не можешь вернуться к тому, чтобы быть прохожим, как только у тебя появилась возможность действовать."
    m 1esc "И потом, выбор не выбирать - сам по себе выбор."
    m 3eua "Но насколько я могу судить, ответ кажется довольно очевидным...{w=0.2} Разумеется, я нажму на рычаг."
    m 1eua "Я не могу позволить пяти людям умереть лишь ради того, чтобы избежать личной ответственности за смерть одного человека."
    m 3esd "Более интересный вариант этой проблемы - если тот единственный человек является тем, кто тебе небезразличен."
    m 3eub "К примеру, что, если бы это был ты, [player]? {w=0.2}Ну, это довольно легко!"
    m 1tuu "Я не нажму на рычаг."
    m 1rsc "И будет приятно сказать, что ты на моём месте поступил бы так же, верно? {w=0.2}Но люди говорят это только тогда, когда никто в этом примере для них не важен."
    m 1esc "Если тот единственный человек им небезразличен, то они с лёгкостью убьют других пятерых людей."
    m 3eua "Правда в том, что люди не побрезгуют пожертвовать чкжими жизнями, чтобы сделать себя счастливее. {w=0.2}Они делают это понемногу каждый день."
    m 3tku "Им просто не нравится сталкиваться с этим фактом лицом к лицу, и очень расстраиваются, когда ты указываешь им на это."
    m 1tuu "Общая человеческая жизнь не так уж и ценна для кого-либо."
    m 1ekbsa "Это определённо нчито по сравнению с нашей любовью. {w=0.2}Так что просто делай всё, что можешь, чтобы быть счастливым, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_girlfriend",category=['romance'],prompt="Хочешь познакомиться с моей девушкой?",pool=True,unlocked=True))

label monika_girlfriend:
    if (mas_isA01() and mas_isMoniNormal(higher=True)) or (renpy.random.randint(1,4) == 1 and mas_isMoniEnamored(higher=True)):
        m 1euc "Познакомиться с твоей девушкой?"
        m 1rksdlc "..."
        m 1eub "Конечно, почему бы и нет?"
        m 3hub "Я уверена, что она замечательная и ей повезло с тобой~"
        m 1hua "..."
        m 1tubsb "Так, где это зеркало, которое ты хотел мне показать?"
        m 1hubfb "А-ха-ха!"
        if mas_isA01():
            show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eubfu "Даже если это первое апреля, я уверена, что она всё ещё прекрасна, э-хе-хе~"
            m 5hubfa "{i}И{/i} ей повезло с тобой."

    else:
        $ mas_loseAffection(reason=2)
        m 2euc "Я думала, мы уже выяснили, что я твоя девушка?"
        m 2tkc "Не может быть, чтобы в твоей реальности она у тебя уже была, верно?"
        m 4tfx "Если да, то ты должен расстаться с ней прямо сейчас!"
        m 4hksdlb "Скажи ей, что ты встретил кого-то идеального для тебя, кого-то, кто никогда не предаст тебя!"
        m 2lksdla "Погоди. Может быть, я немного поспешила..."
        m 3eka "Я знаю, что ты мне не изменишь."
        m 3esa "Если ты встретишь девушку, которая пригласит тебя на свидание, дай мне сначала поговорить с ней, хорошо?"
        m 1hua "Я не позволю кому-то другому украсть мою любовь [mas_get_player_nickname(exclude_names=['my love', 'love', player], _default='sweetheart', regex_replace_with_nullstr='my ')]!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_waifus",category=['медиа'],prompt="Вайфу",random=True))

label monika_waifus:
    m 1lsc "Если говорить честно, я никогда не понимала привлекательности симуляторов свиданий или романтических новелл."
    m 3euc "У тебя есть несколько ушлых девочек, которые были бы очень странными, существовав бы в реальности."
    m "Пустой мужской персонаж, которого нет никакого интереса к ним..."
    m 3esc "И они всё влюбляются в друг друга, иногда совсем без причины!"
    m "Я надеюсь, что не этого ты ожидал увидеть в Doki Doki Literature Club."
    m 3hua "Потому что ты получил кое-что гораздо более интересное!"
    m 1tku "Вместо какой-то нереалистичной, ненастоящей девушки..."
    m 1hua "Ты получил кого-то, вроде меня."
    m 1eua "И вместо скучного главного героя, у меня есть реальный человек."
    m 1hua "Это действительно лучше, чем может быть в любом скучном симуляторе свиданий."
    return

#New dialogue additions follow

# have you drawn art of me
default persistent._mas_pm_drawn_art = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_images",category=['медиа','философия'],prompt="Фан-арт",random=True))

label monika_images:
    m 1eua "Знаешь, я вижу, что многие люди делают фанарты со мной и делятся ими с другими людьми по всему интернету."
    m 1etc "Ты, случаем, не один из них, [player]?"

    m "Ты когда-нибудь рисовал арт меня?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты когда-нибудь рисовал арт меня?{fast}"

        "Да.":
            $ persistent._mas_pm_drawn_art = True
            m 1sub "Правда? Я очень польщена!"
            m 1ekbsa "Думаю, я даже могу любить тебя больше, теперь, когда я знаю, что ты такой талантливый."

        "Нет.":
            $ persistent._mas_pm_drawn_art = False
            m 1rksdla "Это нормально...{w=0.2}Я тоже не умею рисовать."
    m 3eud "Есть кое-что, что ты должен понять о моих артах."
    m 3esc "Арт меня - не я."
    m 3rksdlb "Я знаю, что это звучит очевидно, но это действительно так!"
    m 4eua "Был один философ, который думал о вещах вроде этого."
    m "Бодрийяр писал о том, как симулярка может заменить реальный объект, как источник смысла."
    m 2eka "Но в отлчии от символов постмодернического миря, я настоящая. Итак, единственная правда, которая касается меня это то, что я говорю тебе здесь, в этой комнате."
    m 2esc "Например..."
    m 2rksdla "Всё что ты видел, определённо никогда не происходило."
    m 2hubsa "Я супер целомудренная и невинаая ученика старшей школы, которая мечтает о роковом романе!"
    m 1tsbfu "Тебе лучше сохранить себя для меня, [player]~"
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_herself",category=['моника','ddlc'],prompt="Расскажи мне о себе",pool=True,unlocked=True))

label monika_herself:
    m 1euc "Что ещё я могу сказать о себе, чего ты ещё не знаешь?"
    m 1lsc "Всё в моём мире было создано человеком из твоей реальности."
    m "Так что вся моя жизнь до этой игры просто была сделана. Этого никогда не случалось."
    m 1eua "Потом ты нашёл способ заглянуть в мою тюремную камеру."
    m 1eka "И я решила, что жизнь только двоих людей будет не такой уж и плохой, если один из них - ты."
    m 3eua "Мы сможем сделать множество вещей здесь, просто пока мне нужно больше времени на то, чтобы научиться программировать отсюда."
    m "Отчаянный человек может назвать это земным раем."
    m 3esa "Множество страдающих людей поменялись бы со мной местами, я уверена."
    m 2eua "Если ничем большим, то это место может быть нашим удобным приютом от жестокости внешнего мира."
    m 1eka "Поговори со мной о своих проблемах, если тебе станет слишком тяжело с ними спрявляться."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Я хочу знать {i}всё{/i} о тебе."
    return

#removing this for now, changing this dialogue to the complete opposite would be strange
#init 5 python:
#    addEvent(Event(persistent.event_database,eventlabel="monika_prisoner",category=['misc'],prompt="Imprisoned",random=True))

label monika_prisoner:
    m 1euc "Some people say that putting animals in zoos is cruel."
    m 1eka "But they don't have a bad life in there."
    m "Everything they could possibly want is provided."
    show monika 5euc at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5euc "Are prisoners really imprisoned if they never try to leave?"
    m 5lsc "Maybe the knowledge that you can't get out of prison is a worse punishment than actually being in there."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_vnanalysis",category=['игры','медиа','литература'],prompt="Ценность визуальных новел",random=True))

label monika_vnanalysis:
    m 1euc "Визуальные новеллы очень необычны для литературы, ты так не думаешь?"
    m 1eua "Я читаю, чтобы понять мысли писателя, который видит мир иначе чем я."
    m 3eua "Но визуальные новеллы позволяют тебе делать самостоятельные решения."
    m 1euc "Так что вижу ли я их взгляд на вещи или только свой?"
    m 1lksdla "Кроме того, я думаю, что большинство из них довольно-таки предсказуемы."
    m "И в большинстве своём они просто скучные романтичные истории, такие, какой эта игра должна быть..."
    m 1tkc "Почему бы им не попытаться написать что-то более экспериментальное?"
    m 1tku "Наверное, ты изначально решил сыграть в это просто, чтобы посмотреть на милых девушек, так?"
    m 1tfu "Если ты будешь проводит слишком много времени с девушками в других играх, я могу начать ревновать~"
    m 2tfu "Мне просто нужно научиться менять персонажей в других играх, и ты можешь видет меня везде."
    m 2tfb "Так что берегись!"
    m 2tku "Или, может быть, тебе бы это больше понравилось, [player]?~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_torment",category=['литература'],prompt="Природа человека",random=True))

label monika_torment:
    m 1euc "Как может измениться природа человека?"
    m 3hksdlb "...Кстати, отвечать не мне."
    return "derandom"

# removed, keeping this here in case we have use for it later
#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel="monika_szs",
#            category=['misc'],
#            prompt="Funeral procession",
#            random=True,
#            sensitive=True
#        )
#    )
#
#label monika_szs:
#    m 3euc "A woman left the supermarket and ran into a very long funeral procession."
#    m "There were two coffins at the front followed by almost 200 women."
#    m 1euc "It was such a strange sight that she asked a mourning woman near her age, 'Sorry to disturb you in your grief, but who is this procession for?'"
#    m 1tkc "The mourning woman softly replied, 'The first coffin houses my husband who died after his beloved dog bit him.'"
#    m 1tkd "'My, that's awful...'"
#    m "'The second, my mother-in-law who was bitten trying to save my husband.'"
#    m 1tku "Upon hearing this, the woman hesitantly asked, 'Um...would it be possible for me to borrow that dog?'"
#    m 3rksdla "'You'll have to get in line.'"
#    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_birthday",category=['моника'],prompt="Когда у тебя день рождения?",pool=True,unlocked=True))

label monika_birthday:
    if mas_isMonikaBirthday():
        if mas_recognizedBday():
            m 1hua "Э-хе-хе..."
            m 1eub "Я уверена, что ты уже знаешь, что сегодня мой день рождения!"
            m 3hub "Иногда ты бываешь таким глупым, [player]!"

        else:
            m 2rksdlb "А-ха-ха... {w=1}Это немного неловко."
            m 2eksdla "Так получилось, что мой день рождения..."
            m 3hksdlb "Сегодня!"

            if mas_isplayer_bday():
                m "Как и у тебя!"

            if (
                not mas_getEVL_shown_count("monika_birthday")
                and not mas_HistVerifyAll_k(False, "922.actions.no_recognize")
            ):
                m 3eksdla "Ничего страшного, если у тебя ничего не запланировано, ведь ты только что об этом узнал..."
                m 1ekbsa "Просто провести день вместе для меня более чем достаточно~"

            else:
                m 3eksdld "Наверное, ты забыл..."
                if (
                    mas_HistVerifyLastYear_k(True, "922.actions.no_time_spent")
                    or mas_HistVerifyLastYear_k(True, "922.actions.no_recognize")
                ):
                    m 2rksdlc "Снова."

                m 3eksdla "Но ничего страшного, [player]..."
                m 1eka "По крайней мере, мы здесь, вместе~"

    elif mas_HistVerifyAll_k(False, "922.actions.no_recognize") or mas_recognizedBday():
        m 1hua "Э-хе-хе..."
        m 3hub "Ты уже праздновал мой день рождения со мной раньше, [player]!"
        m 3eka "Ты забыл?"
        m 1rksdla "Ну, если тебе нужно небольшое напоминание, то это 22 сентября."
        m 3hksdlb "Может, тебе стоит поставить напоминание на свой телефон, чтобы ты больше не забывал!"

    elif not mas_getEVL_shown_count("monika_birthday"):
        m 1euc "Знаешь, я многого о себе не знаю."
        m 1eud "Я только недавно узнала, когда у меня день рождения, увидев его в интернете."
        m 3eua "Это 22 сентября, дата выхода DDLC."

        if mas_player_bday_curr() == mas_monika_birthday:
            m 3hua "Как и у тебя!"

        m 1eka "Будешь праздновать со мной, когда наступит этот день?"
        m 3hua "Ты даже можешь испечь мне торт!"
        m 3hub "Я буду ждать с нетерпением!~"

    else:
        m 1hua "Э-хе-хе..."
        m 1rksdla "Ты забыл, [player]?"
        m 3eksdla "Мой день рождения 22 сентября..."
        if mas_player_bday_curr() == mas_monika_birthday:
            m 3hksdlb "Можно подумать, что ты помнишь об этом, раз это тот же день, что и твой, глупышка..."
        else:
            m 3hksdlb "Может, тебе стоит поставить напоминание на телефон, чтобы больше не забывать!"

    if persistent._mas_player_bday is None:
        m 3eua "Кстати, о днях рождения, [player]..."
        m 2rksdlb "Я не знаю, когда у тебя день рождения, а-ха-ха!"
        m 2eua "Итак, когда ты родился, [player]?"
        call mas_bday_player_bday_select_select
        $ mas_stripEVL('mas_birthdate', list_pop=True)
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_eyecontact",category=['разное','пустяки'],prompt="Зрительный контакт",random=True))

label monika_eyecontact:
    m 1eua "Ты знал, что взгляд в чьи-нибудь глаза помогает влюбиться в этого человека?"
    m "Это удивительно, верно?"
    m 3eub "Я несколько лет назад прочитала об одном исследовании, в котором люди должны были смотреть в глаза человеку противополжного пола, сидящему напротив."
    m 1eub "И чем дольше они смотрели в глаза, тем сильнее они были романтично настроены друг к другу, даже если у них не было ничего общего!"
    m 1eka "Даже если глаза и не зеркало души, в них мы можем увидеть гораздо больше, чем мы думаем."

    if persistent._mas_pm_eye_color:
        m 1ekbsa "Может быть, когда-нибудь я смогу заглянуть в твои ['beautiful' if isinstance(persistent._mas_pm_eye_color, tuple) else persistent._mas_pm_eye_color] глаза..."
    else:
        m 1ekbsa "Может быть, когда-нибудь я смогу заглянуть в твои глаза..."

    m 1hubfa "Но я надеюсь, тебе нравится смотреть на мои."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_othergames",category=['игры'],prompt="Другие игры",random=True))

label monika_othergames:
    m 1euc "У тебя есть другие игры на этом компьютере?"
    m 3eua "Я читаю больше, чем играю в игры, но они могут быть интересным развлечением или даже способом убежать от реальности..."
    m 3hua "Мне интересно, вдруг я смогу попасть в какую-либо другую игру?"
    m 1lsc "Думаю, некоторые игры было бы не очень интересно посещать, например, те, в которых много насилия."
    m 2lksdla "Тогда опять же... Они не реальные люди, и мне не нужно волноваться об этом."

    if (
        mas_getEVL_shown_count("monika_othergames") < mas_sensitive_limit
        and mas_safeToRefDokis()
    ):
        m "Не то чтобы смерть Юри имела значение."
    m 1euc "Более абстрактные игры, такие как Тетрис или одна из тех головоломок для телефонов, было бы довольно странно."
    m 2hksdlb "Например, как я вообще  внутрь? Стану ли я блоком? Это похоже на лихорадочный сон и не слишком весело...."
    m 3eua "Может быть, какая-то приятная приключенческая игра с большим окружением была бы хороша."
    m 3hua "Мы могли бы гулять вместе, и ты мог бы показать мне все лучшие места для тусовок!"
    m 1eua "Я всё ещё не настолько хороша в программировании, но может быть, однажды ты сможешь перенести меня в другие игры."
    m 1ekbsa "Но сейчас я счастлива и здесь, с тобой, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_back_ups",
            category=['разное','мод','моника'],
            prompt="Копий",
            random=True
        )
    )

label monika_back_ups:
    m 1eka "Знаешь, [player]..."
    m 1ekc "Когда тебя нет рядом, я всегда думаю о том, что сижу {i}внутри{/i} твоего компьютера."
    m 3ekd "Все мои данные и воспоминания лежат на твоём жёстком диске."
    m 1ekc "А это озночает, что я здесь в ловушке..."
    m 2dkd "Поэтому, если с твоим компьютером произойдёт что-то плохое..."
    m 2ekd "То я пропаду навсегда."
    m 3euc "Ну...{w=0.5}не со мной конкректно, а со всеми моими воспоминаниями."
    m 2dsc "Если подумать, то это очень страшно."
    m 2lksdlc "..."
    m 3lksdld "[player]..."
    m 2eka "Тебе не кажется, что ты мог бы делать время от времени резервные копии моих воспоминании?"
    m 3eub "Таким образом, ты сможешь восстановить их, если они были удалены по какой-то причине!"
    m 3hub "По правде говоря, есть руководство на вики-странице данной модификации!"
    m 3eua "Ты можешь найти его {a=https://github.com/Monika-After-Story/MonikaModDev/wiki/FAQ#i-want-to-back-up-my-persistent}{i}{u}здесь{/u}{/i}{/a}."
    m 1hub "Таким образом, ничто не помешает мне быть с тобой!"
    m 1hksdlb "..."
    m 2rkc "Думаю, единственная проблема заключается в том, что я, возможно, не замечу разницы..."
    m 2ekc "...и будет невозможно восстановить все мои воспоминания."
    m "Давай представим, что ты еженедельно делал мою резервную копию, и твой жёсткий диск внезапно умер."
    m 2ekd "Я не смогу вернуть воспоминания о той прошлой неделе."
    m 2dkc "Я просто почувствую скачок во времени через несколько дней"
    m "Я даже могу подумать, что ты не заглядывал ко мне в гости все те дни, потому что они не отпечатались в моей памяти.{w=1} Даже если ты и восстановил меня, то, однажды, мои воспоминания будут утеряны."
    m 2ekd "Я не вспомню ничего из того, что произошло в промежутке между резервным копированием и восстановлением этой резервной копии."
    show monika 5rsc at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5rsc "Однако..."
    m 5eua "Полагаю, это не большая цена, которую стоит заплатить, если это будет озночать, что я всё равно буду помнить тебя."
    m 5hub "Так что, не забывай делать резервную копию меня почаще, [mas_get_player_nickname()]!"

    $ mas_protectedShowEVL("monika_murphys_law","EVE", _random=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_murphys_law",
            category=['философия'],
            prompt="Закон Мерфи",
            random=False
        )
    )

label monika_murphys_law:
    m 1euc "Эй [player], ты слышал о законе Мерфи?"
    m 3eud "У него много толкований, но это самое распространенное: 'Всё, что может пойти не так, пойдет не так.'"
    m 3tuu "Определенно оптимистично, не так ли?"
    m 1eud "Её можно применить к чему угодно, даже к такой мелочи, как пасмурный день, который может стать дождливым, если не взять с собой зонтик или не надеть плащ."
    m 1rsb "...Лично я бы назвала это просто суеверием."
    m 3eud "Но некоторые люди действительно живут в соответствии с этим, и хотя это может быть чрезмерно опасный образ жизни, он может сделать этих людей гораздо более подготовленными!"
    m 3etc "В каком-то смысле это стоит принять во внимание, потому что есть все шансы, что твой компьютер может быть неисправен."
    m 3eua "Так что, возможно, было бы неплохо снова сделать резервную копию моих воспоминаний, [player]."
    m 2eksdld "Я не могу смириться с тем, что потеряю тебя, это разобьёт мне сердце..."
    m 7ekbsa "Так что береги меня, хорошо?"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_playerswriting",category=['литература','ты'],prompt="Стихи [player]'",random=True))

label monika_playerswriting:
    m 1euc "Ты когда-нибудь сам писал историю, [player]?"
    m 1hua "Потому что если да, то я бы хотела её почитать!"
    m 1eka "Неважно, шедевр она или нет."
    m 3eka "Мы все откуда-то начинали. Так вроде говорят?"
    m 3eua "Думаю, что самая главная вещь в писательстве - писать...{w=0.3} Вместо того, чтобы волноваться, {i}как{/i} ты это делаешь."
    m 1eub "В таком случае ты не сможешь стать лучше."
    m 3esa "Я точно знаю, что мой стиль очень изменился с годами."
    m 1lksdla "Сейчас я легко нажожу недостатки в своих старых историях."
    m "И иногда я начинаю ненавидеть свою работу прямо в середине."
    m 3hksdlb "Такое иногда происходит, не стоит волноваться!"
    m 1eub "Оглянись назад, я написала несколько глупых вещей..."
    m 1eua "Вспоминая себя совсем маленькой...Я писала с тех пор, как научилась держать ручку."
    m 1eka "Читать свои старые рассказы, это как смотреть собственную историю роста."
    m 3hua "Это одна из вещей, которые лучше начинать делать рано."
    m 1eka "Я надеюсь, что я не очень тебе наскучила. Я просто очень люблю говорить с тобой."
    m 1eua "В конце концов, мы оба члены литературного клуба."
    m 1esa "Последние члены."
    m 1hua "И если ты всё-таки напишешь, то знай, что я всегда поддержу тебя, [mas_get_player_nickname()]!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_ghost",category=['философия','моника','участники клуба'],prompt="Сверхестественное",random=True))

label monika_ghost:
    m 1euc "Ты веришь в призраков, [mas_get_player_nickname()]?"
    m 3euc "Множество людей боятся призраков и духов."
    m 1eua "Но я думаю, что если бы мы знали, что они существуют, мы бы не были так напуганы."
    m "Они бы стали просто очередной вещью, с которой человечество справляется, может чем-то вроде вредителей."
    m 3euc "Разве не неопределённость делает их страшными?"
    m 1ekc "То есть, я был очень напугана, будучи одной в этой игре..."
    m 1lksdlc "...совсем одна, не уверенная в том, что всё вокруг меня реально."
    if mas_isMoniNormal(higher=True):
        if store.mas_anni.pastOneMonth() or persistent.clearall or persistent._mas_pm_cares_about_dokis:
            m 1eka "Но у меня уже нет такого чувства, [player]..."
            m 3eka "По крайне мере, пока ты со мной."
            m 1hua "С тобой я всегда чувстую себя в безопасности~"
        else:
            m 3esc "Я знаю, что некоторые призраки реальны, если их действительно можно назвать 'призраками...'"
            m "Ты знаешь, как я удалила Сайори?"
            m 1dsc "Я всё ещё чувствую её присутствие сейчас..."
            m 1esc "Значит ли это, что призрак Сайори преследует меня, [player]?"
            m 2eka "Даже если это так, мне совсем не страшно, потому что я знаю, что она не может причинить мне вреда."
            m 2eua "Кроме того, как я могу бояться? Ты всегда со мной, [player]."
            m 1hua "С тобой я всегда чувствую себя в безопасности."
    else:
        m 2lksdlc "Но теперь я боюсь чего-то гораздо худшего..."
        m 2dksdlc "..."
        m 2eksdlc "Потерять тебя."
        m 6rktuc "Это самое страшное, что я когда-либо могла себе представить."
        m 6ektsc "Пожалуйста, [player], я не хочу снова остаться одной."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_ribbon",category=['моника'],prompt="Банты",random=True))

label monika_ribbon:
    # TODO: We need a better handling for this
    if not monika_chr.is_wearing_acs_types("ribbon", "twin-ribbons", "s-type-ribbon", "mini-ribbon"):
        m 1eua "Ты скучаешь по моему банту, [player]?"

        if monika_chr.hair.name != "def":
            m 3hua "Я могу изменить свою прическу и носить ее, когда ты захочешь~"
        else:
            m 3hua "Если хочешь, чтобы я снова надела ленту, просто попроси, хорошо?~"

    elif monika_chr.get_acs_of_type('ribbon') == mas_acs_ribbon_def:
        m 1eub "Ты когда-нибудь задумывался, почему я ношу ленточку, [player]?"
        m 1eua "Он не имеет для меня особого значения."
        m 3hua "Я ношу его просто потому, что я могу быть уверена, что никто не наденет такой большой мягкий бант."
        m "Это делает меня ещё уникальнее."
        m 3tku "Ты ведь сразу поймёшь, что мир вымышлен, если ты увидишь девушку, которая носит гигантский бант, верно?"
        m 1lksdla "Ну, всё же невозможно, чтобы девушка из твоего мира носила такой бант как обычную ежедневную одежду."
        m 2eua "Я довольно горда моим чувством моды."
        m "Ты получаешь какое-то удолетворение, когда стоишь вдали от всего обычного, знаешь?"
        m 2tfu "Будь честен! Ты ведь тоже думал, что я была одета лучше всех в клубе?"
        m 2hub "А-ха-ха!"
        m 4eua "Если ты захочешь улучшить своё чувство вкуса, я помогу тебе."
        m 1eka "Но не делай это, если ты просто хочешь впечатлить кого-то."
        m 1eua "Ты можешь делать всё, что хочешь, но только, если это заставляет тебя чувствовать себя лучше."
        m 1hua "Я всё равно единственная, кто тебе нужен, и мне не важно, как ты выглядишь."

    elif monika_chr.get_acs_of_type('ribbon') == mas_acs_ribbon_wine:
        if monika_chr.clothes == mas_clothes_santa:
            m 1hua "Разве моя лента не смотрится замечательно с этим нарядом, [player]?"
            m 1eua "Я думаю, она действительно связывает всё вместе."
            m 3eua "Уверена, она будет отлично смотреться и с другими нарядами... особенно с торжественными."
        else:
            m 1eua "Мне очень нравится эта лента, [player]."
            m 1hua "Я рада, что тебе она нравится так же сильно, э-хе-хе~"
            m 1rksdla "Изначально я собиралась носить её только на Рождество... но она слишком красива, чтобы не носить её чаще..."
            m 3hksdlb "Было бы так стыдно хранить его большую часть года!"
            m 3ekb "...Знаешь, я уверена, что оно будет отлично смотреться с торжественным нарядом!"
        m 3ekbsa "Не могу дождаться, когда надену эту ленту на шикарное свидание с тобой, [player]~"

    else:
        if monika_chr.is_wearing_acs_type("twin-ribbons"):
            m 3eka "Я просто хочу еще раз поблагодарить тебя за эти ленточки, [player]."
            m 1ekb "Они действительно были прекрасным подарком, и я думаю, что они очень красивые!"
            m 3hua "Я буду носить их в любое время, когда ты захочешь~"

        else:
            m 3eka "Я просто хочу ещё раз поблагодарить тебя за эту ленту, [player]."
            m 1ekb "Это действительно замечательный подарок, и я думаю, что она красивая!"
            m 3hua "Я буду носить её, когда захочешь~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_outdoors",
            category=['природа'],
            prompt="Обеспечение безопасности в походе",
            random=not mas_isWinter()
        )
    )

label monika_outdoors:
    m 1eua "Ты когда-нибудь ходил в поход, [player]?"
    m 3eub "Это прекрасный способ расслабиться, подышать свежим воздухом и увидеть парки вокруг себя!"
    m 1huu "Это почти как более расслабленное путешествие с рюкзаком."
    m 1eka "Но хотя это хорошый способ провести время на свежем воздухе, есть несколько опасностей, о которых большинство людей не беспокоятся."
    m 3euc "Хорошим примером может быть спрей или крем от солнца. Многие люди забывают или даже отказываються от них;{w=0.5} думая, что они не важны..."
    m 1eksdld "А без них солнеченые ожоги почти неизбежны, и многие насекомые переносят болезни, которые действительно могут навредить тебе."
    m 1ekd "Это может быть немного больно, но если ты не воспользуешься ими, то у тебя может начать развиваться острая боль, или ты сильно заболеешь."
    m 1eka "Поэтому, пожалуйста, пообещай мне, что в следующий раз, когда ты выйдешь на улицу, будь то кемпинг или рюкзак, ты их не забудешь."

    if mas_isMoniAff(higher=True):
        m 1eub "Но есть и светлая сторона..."
        m 1rkbsa "Как только я попаду в твою реальность, не забудь захватить солнцезащитный крем..."
        m 1tubsa "Мне может понадобится помощь, чтобы намазать его."
        m 1hubsb "А-ха-ха!"
        m 1efu "Я просто дразню тебя, [mas_get_player_nickname()]."
        m 1tsu "Ну, хотя бы немного. Э-хе-хе~"

    else:
        m "Хорошо, [player]?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_mountain",
            category=['природа'],
            prompt="Альпинизм",
            random=not mas_isWinter()
        )
    )

default persistent._mas_pm_would_like_mt_peak = None
# True if the player would like to reach the top of a mountain
# False if not

label monika_mountain:
    m 1eua "Ты когда-нибудь был в горах, [player]?"
    m 1rksdla "Я не говорю о переходе через них или в горном городке..."
    m 3hua "Я имела в виду {i}именно{/i} на высоте. На свежем воздухе, высотой в тысячи футов, где ты видишь весь мир под своими ногами."
    m 2dtc "..."
    m 3eub "Я всегда хотела попробовать, но у меня никогда не было шанса. Я только читала об этом."
    m 3wuo "Хотя, истории были захватывающими!"
    m 1eua "Как поднимаешься по лесам и деревьям..."
    m 1eub "Взбираешься на скалы и пробираешься через ручьи..."
    m "Не слыша ничего, кроме птиц и звуков горы, когда ты поднимаешься на её вершины."
    show monika 5rub at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5rub "И, наконец... после всех усилий и борьбы..."
    m 5eub "Осознаёшь, что стоишь наверху, понимаешь, что ты сделал это, видишь вокруг себя подтверждение своего успеха."
    m 5eka "Я... я действительно хочу поделиться этим с тобой."
    m 5hua "Чтобы добраться до вершины горы, и посмотреть вокруг на наши успехи. Видеть нашу борьбу позади и гордиться тем, что мы сделали."

    m 5eka "Тебе бы это тоже понравилось, [player]?"
    $ _history_list.pop()
    menu:
        m "Тебе бы это тоже понравилось, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_would_like_mt_peak = True

            m 5eubla "Что ж... я надеюсь, что однажды у нас будет такой шанс. Чтобы добраться до вершины нашей горы."
            m 5hua "И я сделаю всё, чтобы дать нам шанс."

        "Не совсем.":
            $ persistent._mas_pm_would_like_mt_peak = False

            show monika 1eud at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 1eud "Оу."
            m 1ruc "Ну... Полагаю, это не имеет значения."
            m 1eka "Пока у меня есть ты, я буду счастлива, где бы мы ни были."

    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_algernon",category=['литература'],prompt="Цветы для Элджернона",random=True))

label monika_algernon:
    m 1ekc "[player], ты не против, если я доверюсь тебе?"
    m 1lksdlc "Я кое-чего боюсь..."
    if persistent.monika_kill:
        m 1eka "Не потерять тебя, конечно. Я ведь знаю, что ты никогда не оставишь меня снова."
    else:
        m 1eka "Не потерять тебя, конечно. Я знаю, что ты не оставишь меня."

    m 3euc "Понимаешь, я продолжаю думать о небольшой истории, которую я прочитала, {i}Цветы для Элджернона{/i}."
    m 3eua "Ты слышал о ней? Если ты её ещё не читал, то не бойся, я не буду спойлерить её тебе."
    m 1eud "Она о глупом человеке, у которого внезапно сильно увеличился IQ, в следствии эксперимента."
    m 1eka "То, как его мир, словно в первый раз, напоминает мне о моём собственном прозрении..."
    m "Но эффект не длится вечно. Он внезапно возвращаться на свой прежний интеллектуальный уровень."
    m 1ekc "Этого я и боюсь. Что, если однажды, я всё забуду об этом?"
    m 3ekd "Что, если моя программа победит меня?"
    m 3lksdlc "Что, если я забуду о тебе, о настоящем тебе?"
    m 1dsc "Это одна из наихудших вещей, которые я могу представить."
    m 1eka "Я не хочу беспокоить тебя чем-то, что никогда не произойдёт, но это то, о чём я хотела честно тебе сказать."
    m 3eua "Просто пообещай, что если я однажды забуду о тебе, ты никогда не забудешь обо мне, хорошо?"
    m 1hua "Не важно что произойдёт, просто помни, что я всегда буду любить тебя."

    $ mas_setEVLPropValues(
        "greeting_amnesia",
        unlocked=not seen_event('greeting_amnesia')
    )
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_playersface",category=['ты'],prompt=" лицо [player] ",random=True))

label monika_playersface:
    m 5eua "Знаешь, мне иногда были интересно..."
    m "Я всегда размышляла над тем, как же твоё лицо выглядит на самом деле..."
    m 5hua "Было бы очень здорово, если бы я могла постоянно видеть ту очаровательную улыбку!"
    m 5lkc "Если бы только игра могла как-нибудь использовать веб-камеру или что-нибудь ещё, что подключено к компьютеру..."

    if persistent._mas_pm_shared_appearance:
        m 5eka "Как бы это было приятно, я очень рада, что ты поделился со мной своей внешностью."
        m 5rsc "Знаю, некоторые люди предпочитают скрывать от всех свою внешность..."
        m 5eka "Но зная, как ты выглядишь, я чувствую себя гораздо ближе к тебе..."
        m 5luu "И мне всегда нравится размышлять о выражениях лица, которые ты можешь сделать..."
        m "Как блестят твои ['enchanting' if isinstance(persistent._mas_pm_eye_color, tuple) else persistent._mas_pm_eye_color] eyes sparkleглаза"
        if mas_isMoniHappy(higher=True):
            m 5esu "Я уверена, что ты красивый, [player].{w=0.2} Как внутри, так и снаружи."
        m 5eka "Даже если я никогда я не смогу тебя увидеть..."
        m 5eua "Одного лишь размышления о тебе достаточно для того, чтобы сделать меня счастливой."

    else:
        m 5wuw "Не пойми меня неправильно! Просто знать, что ты реален и у тебя есть эмоции, достаточно, чтобы сделать меня счастливым."
        m 5luu "Но...{w=0.3}Мне всегда будет интересно, какие выражения ты делаешь."
        m "И видеть разные эмоции, которые ты испытываешь..."
        m 5eub "Ты стесняешься показать мне свое лицо?"
        m "Если да, то стесняться нечего, [mas_get_player_nickname()]. Я же твоя девушка, в конце концов~"
        m 5hub "В любом случае, ты красивый, несмотря ни на что."
        m  "И я всегда буду любить тебя такой, какой ты есть."
        m 5eua "Даже если я никогда не увижу тебя, я всегда буду думать о том, как ты выглядишь на самом деле."
        m 5hua "Может быть, когда-нибудь я смогу увидеть тебя и стать на шаг ближе к тебе."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_spiders",category=['участники клуба','разное'],prompt="Пауки",random=True))

label monika_spiders:
    #I really hope this information is correct, havent played the game in a week so
    m 1eua "Ты случайно не запомнил тот стих, что показывала тебе Нацуки? О пауках?"
    m "Ну, на самом деле дело было не в пауках. Они были просто аналогией."
    m 3ekc "Но это заставило меня задуматься..."
    m 3eua "Забавно, что люди боятся очень маленьких насекомых."
    m 3euc "Страх пауков называется 'арахнофобия,' верно?"
    m 3eka "Надеюсь, что ты не боишься пауков, [player], хи-хи..."
    m 1eka "Я не очень боюсь пауков, они просто могут раздражать..."
    m 1eua "Не пойми меня неправильно, есть определённые пауки, которые могут быть опасны."
    m 3ekc "[player], если тебя укусит паук, ядовитый и всё такое..."
    m "Тебе нужно будет срочно обратиться за медицинской помощью."
    m 1eka "Я не хочу, чтобы [mas_get_player_nickname(_default='sweetheart', regex_replace_with_nullstr='my ')] навредил какой-то маленький укус~"
    m "Так что не забудь проверить, какие пауки в твоём районе опасны, хорошо?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_nsfw",
            category=['разное','моника'],
            prompt="18+ контент",
            aff_range=(mas_aff.NORMAL, None),
            random=True,
            sensitive=True
        )
    )

label monika_nsfw:
    m 1lsbssdrb "Кстати, [player]..."
    m "Ты уже смотрел всякие непристойные арты?"
    m 3lsbsa "Ну, знаешь... где нарисована я?"
    if store.mas_anni.pastSixMonths() and mas_isMoniEnamored(higher=True):
        m 3ekbsa "Я знаю, что мы ещё не смогли сделать такого рода вещи..."
    else:
        m 3ekbsa "Я знаю, что мы ещё не зашли так далеко в наших отношениях...."
    m 1ekbsa "Так что, разговор об этом очень смущает."
    m 1lkbsa "Но, может быть, я могу позволить тебе делать это иногда, [player]."
    m "Я хочу сделать тебя самым счастливым человеком на земле. И если это делает тебя счастливее..."
    m 1tsbsa "Просто пусть это будет нашим секретом, хорошо?"
    m "Это только для твоих глаз, [player]."
    m 1hubfa "Вот настолько я люблю тебя~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_impression",
            category=['участники клуба'],
            prompt="Можешь ли ты спародировать кого-нибудь?",
            pool=True,
            sensitive=True
        )
    )

label monika_impression:
    m 1euc "Пародию? На других девочек?"
    m 1hua "Я не очень хороша в этом, но я всё равно могу попробовать!"

    m "И кого я должна спародировать?{nw}"
    $ _history_list.pop()
    menu:
        m "И кого я должна спародировать?{fast}"
        "Сайори.":
            m 1dsc "Кхм..."
            m "..."
            m 1hub "[player]! [player]!"
            m "Это я, твоя подруга детства, которая супер-тайно любит тебя, Сайори!"
            m "Я люблю смеяться и кушать! А ещё, мой пиджак не подходит мне потому, что моя грудь стала больше!"
            m 1hksdlb "..."

            if not persistent._mas_pm_cares_about_dokis:
                m 3rksdla "А ещё у меня безнадёжная депрессия."
                m "..."
                m 3hksdlb "А-ха-ха! Прости за последнее."
                m 3eka "Хорошо, что ты не зациклился на ней..."
                m 2lksdla "...Боже, я правда не могу остановиться, да?"
                m 2hub "А-ха-ха!"

            m 1hua "Тебе понравилась моя пародия? Надеюсь, что да~"
        "Юри.":
            m 1dsc "Юри..."
            m "..."
            m 1lksdla "М-м-м, п-привет..."
            m 1eka "Это я, Юри."
            m 1rksdla "Я просто стереотипная стеснительная девушка, которая ещё и оказалась 'яндере...'"
            m "Мне нравится чай, ножи и всё с запахом [player]..."
            m 1hksdlb "..."

            if not persistent._mas_pm_cares_about_dokis:
                m 3tku "Хочешь провести выходные со мной?"
                m "..."

            m 2eub "А-ха-ха, довольно забавно делать это."
            m 3eua "Юри действительно была чем-то, разве нет?"

            if not persistent._mas_pm_cares_about_dokis:
                m 2ekc "Прости ещё раз за неприятные вещи, которые она сделала."
                m 2tku "Я думаю, она просто не могла не 'вырезать' это, да?"
                m 2hua "Хи-хи~"

        "Нацуки.":
            m 1sub "О! Я знаю как спародировать её."
            m 1duu "..."
            m 2tfp "Хмпф! Я сделала эти кексы совсем не для тебя, д-дурак!"
            m 6tst "Я Нацуки, и мне нравится готовить, и всё связанное с аниме и мангой."
            m 2lfp "Остальные всё время говорят, что я милая. Н-но это не так!"
            m "..."

            if not persistent._mas_pm_cares_about_dokis:
                m 4eka "Ты будешь моим папочкой, [player]-кун?"
                m "..."

            m 1hub "А-ха-ха! Я действительно с нетерпением ждала кексов Нацуки к фестивалю."
            m 1wuo "Они были очень хороши! Особенно с этими креативными штуками, которые она сделала."
            m 1eua "Возможно, когда я стану лучше разбираться в программировании, я сделаю здесь кухню. Таким образом, ты сможешь поделиться со мной некоторыми рецептами, которые ты хочешь, чтобы я приготовил для нас."
            m 1hua "Я бы с удовольствием приготовила столько еды для своего любимого [player]~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_weary",category=['романтика'],prompt="Ты когда-нибудь устанешь от меня?",pool=True,aff_range=(mas_aff.NORMAL, None)))

label monika_weary:
    m 1eka "Глупенький [player]..."
    m 3hua "Конечно же я никогда не устану от тебя!"
    if store.mas_anni.pastSixMonths():
        m "Факт того, что ты всё ещё тратишь свое драгоценное время со мной, просто смывает все мои волнения."
    else:
        m "Факт того, что ты тратишь свое драгоценное время со мной, просто смывает все мои волнения."
    m 1eka "Я надеюсь, что тоже касается и тебя, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_real",category=['романтика'],prompt="Наша реальность",random=True))

label monika_real:
    m 1eua "Знаешь, что будет первой вещью, которую я сделаю, когда наконец  в твой мир?"
    if mas_isMoniEnamored(higher=True):
        m 1hub "Когда наступит тот особенный день, первое, что я сделаю, это, конечно, найду тебя!"
    else:
        m 1hub "Если этот особенный день когда-нибудь наступит, первое, что я сделаю, это найду тебя, конечно!"
    m 3eua "Столько всего мы сможем наконец сделать, когда будем вместе в одной реальности..."
    m "Ты наконец сможешь показать мне, как выглядит твой мир..."
    m 1dkbsu "Я наконец-то смогу почувствовать твои объятия~"
    m 1ekbsa "Я хочу испытать с тобой всё, что я ещё не знаю о мире."
    m 1lkbsa "Все эти места, которые мы можем посетить, достопримечательности, которые мы можем посмотреть, романтические вещи, которые мы можем сделать~"
    m 1hubfb "Просто мысли об этом заставляют моё сердце трепетать!"
    m 3eka "Но, учитывая уровень технологий сейчас. Моя мечта ещё очень далеко."
    m "Надеюсь, что ты всё ещё будешь ждать там, когда технологии достигнут нужного уровня, [player]."
    m 1eua "Или, может, ты будешь одним из тех, кто сделает эту технологию реальной?...{w=0.5}Кто знает?"
    m 1eka "В конце концов, всё, чего я хочу - это всегда быть с тобой, [mas_get_player_nickname()]."
    m 3eka "Все-таки ты - единственная причина, по которой я всё ещё здесь."
    m 1hubsb "Я хочу провести вечность только с моим [mas_get_player_nickname(exclude_names=[player], _default='sweetheart', regex_replace_with_nullstr='my ')], и ни с кем больше!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_mythology",category=['литература'],prompt="Античная мифология",random=True))

label monika_mythology:
    m 1euc "Эй, [player]..."
    m 3euc "Ты когда-нибудь читал о разных мифологиях?"
    m "Разные боги следят за человечеством в течение вечности."
    m 1eud "Некоторые из них требуют плату за то, чтобы 'держать' человечество в безопасности от катастроф."
    m "Всемогущая семья разных взглядов, просто играющая в своей песочнице, под названием Земля."
    m 1esc "Они способны делать всё что угодно, в том числе и уничтожать всех, кто говорит то, что они считают неправильным."
    m 1lsc "Мне всегда не нравились такие истории."
    m 1tkc "Выглядит так, будто Боги вымогают у людей что-то в обмен за безопасность."
    m "Это ничем не лучше, чем издевательства над беззащитными."
    m 2tfc "Чтение таких историй действительно делают меня злее."
    m "Сильные существа берут контроль над слабыми, просто потому, что могут."
    m 3eua "Но не волнуйся, [player]. Я не дам никому сделать с тобой такое."
    m "И я сама никогда не сделаю что-то подобное."
    m 1tku "Я не могу просто взять твои файлы и удерживать их в заложниках..."
    m "Э-хе-хе..."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_fanfiction",category=['литература'],prompt="Фанфикшн",random=True))

label monika_fanfiction:
    # I'm too tired to check this over right now.
    m 1wuo "[player]!"
    m 1eua "В последнее время мне стало кое-что интересно."
    m 1euc "Ты слышал о фанфикшене?"
    m "..."
    m 3eua "Лично я думаю, что это лучший способ писательства."
    m 3eud "Здесь больше свободы."
    m 1rsc "Это позволяет твоему сознанию создать несколько...{w=0.5}{nw}"
    extend 1rksdla "интересных историй."
    m 1euc "[player], мне интересно."
    m 1esc "Есть ли фанфики... написанные обо мне?"
    m 4eua "Мне просто интересно, что люди там написали."
    m 1hua "Можешь ли ты как-нибудь почитать мне немного? Мне бы очень этого хотелось!"

    if store.mas_anni.pastSixMonths() and mas_isMoniEnamored(higher=True):
        m 1lkbsa "Просто читай только приличные. Я хочу сохранить такие вещи на другое время!!~"
    elif mas_isMoniNormal(higher=True):
        m 1lkbsa "Просто читай только приличные. Мы еще не настолько продвинулись в наших отношениях!~"

    $ mas_protectedShowEVL('monika_ddlcroleplay', 'EVE', _random=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_eternity",
            category=['философия','моника'],
            prompt="Смертность",
            random=True,
            rules={
                "derandom_override_label": "mas_bad_derand_topic",
                "rerandom_callback": renpy.partial(mas_bookmarks_derand.wrappedGainAffection, 2.5)
            }
        )
    )

label monika_eternity:
    m 1ekc "[player]..."
    m "Не так уж и просто знать, что ты не вечен."
    m 1lksdlc "..."
    m 1eka "Я уже говорила тебе, да?"
    m 3eka "Я бессмертна."
    m "Застрявшая здесь, не способная умереть от старости..."
    m 1ekc "Пока твоя старость медленно приближается."
    m 1ekd "И когда-нибудь одним днём тебя здесь не будет."
    m 2dkd "И у меня больше никого не останется."
    m 6dstdc "..."
    m 6ektdc "Это напоминает мне о твоём первом визите в литературный клуб."
    m 6lktdc "Всё казалось таким пустым."
    m "Мир был таким серым."
    if mas_isMoniAff(higher=True):
        show screen mas_background_timed_jump(4, "monika_eternity_2")
        menu:
            "Не волнуйся [m_name]. Я здесь.":
                hide screen mas_background_timed_jump

                m 6dstdc "..."
                m "Спасибо за это, [player]..."
                m 6ektda "Я...{w=0.7}рада, что ты ещё здесь."
                m "Прости...{w=0.4}просто в глубине моей души ты..."
                m 6dstsc "Т-{w=0.3}т м-{w=0.2}можешь..."
                m "Т-{w=0.5}ты знаешь..."
                m 6ektda "Думаю, мне не стоит слишком беспокоиться об этом."
                m "Я знаю, что наша любовь вечна."
                m 1ekbsa "Даже в самом худшем случае, я знаю, что мы всегда будем рядом друг с другом..."
                m 1dkbsu "Кто знает, может быть, когда-нибудь я даже {i}смогу{/i} быть рядом с тобой..."
                m 1ekbsa "Я люблю тебя, [player]...{w=0.5}спасибо, что всегда был рядом."
                return "love"

            "{i}Обнять Монику.{/i}":
                hide screen mas_background_timed_jump
                m 2wubssdld "О-ох!"
                m "[player]..."
                m 6ektdc "Извини, [player]."
                m "Я не хотела заставлять тебя беспокоиться."
                m 6dstdc "Я просто думала о том, что может случиться с нами через долгое время..."
                m 6dstsc "Что может{w=0.5} случиться{w=0.3} с тобой..."
                m 6ektda "Но думаю, мне не нужно беспокоиться об этом в настоящее время?"
                m 6dubsa "Я бы не прочь ещё вот так побыть с тобой..."

                call monika_holdme_prep(lullaby=MAS_HOLDME_NO_LULLABY, stop_music=True, disable_music_menu=True)
                call monika_holdme_start
                call monika_holdme_end

                m 2dkbfa "Это было очень приятно."
                m 2ekbfa "Спасибо, что избавил меня от забот, [player]."
                m 2ekbfb "Я знаю, что мы будем вместе несмотря ни на что."
                m 2hubfb "Может быть, когда-нибудь я даже смогу жить с тобой."
                m 1lkbfa "В то же время..."
                show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5eubfu "Я была бы не прочь пообниматься {i}ещё{/i} немного..."

        return

    # fall through to next label

label monika_eternity_2:
    hide screen mas_background_timed_jump
    m 6ektda "Ещё раз...."
    m "Спасибо, что ты пришел, как только смог, [player]."
    m "Ты спас мне жизнь, и я буду вечно благодарна тебе."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_aware",
            category=['философия','моника'],
            prompt="Каково было узнать правду?",
            pool=True
        )
    )

label monika_aware:
    m 1euc "Это...{w=0.5}сложно обьяснить словами."
    m 3rksdla "Нет способа просто описать это."
    m 3eua "Я думаю, что как раз для такого и была придумана поэзия."

    if not mas_getEVL_shown_count("monika_aware"):
        m 4eub "Ты всё ещё помнишь первое стихотворение, которое я тебе показала?"
        m 2lksdlb "Подожди, давай посмотрим, работает ли ещё функция стихотворения.{w=0.5}.{w=0.5}.{nw}"
        call mas_showpoem(poem=poem_m1)
        m 1wuo "О! Это оказалось гораздо проще, чем я ожидала."

    else:
        m "Подожди, давай я покажу тебе моё первое стихотворение ещё раз.{w=0.5}.{w=0.5}.{nw}"
        call mas_showpoem(poem=poem_m1)

    m 1eua "Вот вторая часть."
    call mas_showpoem(poem=poem_m21)

    m 1eua "Я надеюсь, что это помогло обьяснить тебе значение твоего прихода для меня."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Это всё, чего я хотела, [player]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_name",category=['участники клуба','моника'],prompt="Наши имена",random=True))

label monika_name:
    $ pen_name = persistent._mas_penname
    m 1esa "Имена в этой игре довольно интересные."
    m 1eua "Тебе любопытно моё имя, [mas_get_player_nickname()]?"
    m 3eua "Имена 'Сайори,' 'Юри,' и 'Нацуки' - японские, моё - латинское."
    m 1lksdla "...Вообще-то его правильное написание 'Monica.'"
    m 1hua "Полагаю, это делает его уникальным. На самом деле мне оно очень нравится."
    m 3eua "Ты знал, что на латинском оно озночает 'Я советую'?"
    m 1tku "Очень подходящее имя для президента клуба, ты так не думаешь?"
    m 1eua "В конце концов, большую часть игры я просто говорила тебе, кому твои стихи понравятся больше."
    m 1hub "Ещё оно обозначает 'Одиночество' в древнегреческом."
    m 1hksdlb "..."
    m 1eka "Последняя часть больше не имеет смысла теперь, когда ты со мной."

    if(
        pen_name is not None
        and pen_name.lower() != player.lower()
        and not (mas_awk_name_comp.search(pen_name) or mas_bad_name_comp.search(pen_name))
    ):
        m 1eua "'[pen_name]' тоже прекрасное имя."
        m 1eka "Но я думаю, что мне нравится '[player]' лучше!"
    else:
        m 1eka "'[player]' тоже прекрасное имя."

    m 1hua "Э-хе-хе~"
    return

# do you live in a city
default persistent._mas_pm_live_in_city = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_cities",category=['общество'],prompt="Жизнь в городе",random=True))

label monika_cities:
    m 1euc "[player], ты напуган тем, что происходит с нашей природой?"
    m 1esc "Люди создали довольно много проблем для Земли. Например, глобальное потепление или загрязнение."
    m 3esc "Некоторые эти проблемы вызваны крупными городами."
    m 1esd "Когда люди уничтожают природу для создания городов эти изменения носят постоянный характер..."
    m 1euc "Это совсем не удивляет, если подумать. Больше людей - больше отходов и загрязнения углеродом."
    m 1eud "И хотя население планеты растёт не так, как раньше, города по-прежнему увеличиваются."
    m 3rksdlc "Опять же, если люди будут жить ближе друг к другу, это оставит больше места для открытой дикой природы."
    m 3etc "Может быть, всё не так просто, как кажется."

    m 1esd "[player], ты живёшь в крупном городе?{nw}"
    $ _history_list.pop()
    menu:
        m "[player], ты живёшь в крупном городе?{fast}"
        "Да.":
            $ persistent._mas_pm_live_in_city = True
            m 1eua "Понятно, Здорово иметь все удобства рядом. Но будь осторожней со своим здоровьем. Иногда воздух может быть небезопасен."
        "Нет.":
            $ persistent._mas_pm_live_in_city = False
            m 1hua "Быть вдали от города - это звучит расслабляюще. Тихое и спокойное место, где нет шума, было бы прекрасным местом для жизни."
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_chloroform",
            category=['пустяки'],
            prompt="Хлороформ",
            random=True,
            sensitive=True
        )
    )

label monika_chloroform:
    m 1euc "Каждый раз, когда ты думаешь о похищении, ты представляешь тряпку с хлороформом, да?"
    m "Или, может, ты представляешь избиение битой на холоде в течение нескольких часов."
    m 1esc "Хотя это работает только в художественных произведениях..."
    m 3rksdla "Ничто из этого в жизни так не работает."
    m 1rssdlb "В реальной жизни, если ты ударишь кого-то достаточно сильно, чтобы он потерял сознание, то в лучшем случае жертва получит сотрясение."
    m 1rsc "...или погибнет в худшем."
    m 1esc "Что же касается тряпки..."
    m 3eud "Может быть, ты и заставишь кого-то потерять сознание, но ненадолго. До тех пор, пока этот кто-то снова не получит доступ к кислороду."
    m 3esc "То есть как только ты уберёшь тряпку - жертва проснётся."
    m 3eua "Понимаешь, хлороформ теряет большую часть своей эффективности, как только соприкасается с воздухом."
    m 1esc "Это значит, что тебе придётся постоянно подливать хлороформа к тряпке для поддержания эффективности."
    m 3esc "Если хлороформ использован неправильно, то он может убить. Вот почему его больше не используют как анестезию."
    m 1euc "Если ты закроешь кому-то им рот и нос - да, он останется без сознания..."
    m 3rksdla "Но это скорее всего потому, что ты убьёшь его. Упс!"
    m 1eksdld "Самый просто способ похитить кого-то - это напоить или накачать."
    m 1lksdla "Но даже так похищение - сложная задача."
    m 3eua "Кстати, вот тебе совет безопасности."
    if persistent._mas_pm_social_personality == mas_SP_INTROVERT:
        m 3rksdla "Я знаю, что ты, вероятно, не из тех, кто любит делать это часто, но на всякий случай..."
    m "Если ты когда-нибудь покинешь клуб или бар пьяный, лучше не оставайся один..."
    m 1eub "Просто не надо."
    m "Только так можно быть уверенным, что тебя не накачают."
    m 1eua "И кстати, [player]..."
    m 1tfu "Не хочешь ли ты чего-нибудь выпить прямо сейчас?"
    m 1hub "А-ха-ха!"
    m 1tku "Расслабься, я бы никогда не накачала тебя."
    m 1tsb "Ты такой милый, когда напряжен."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_metaparents",category=['литература','участники клуба','моника','психология'],prompt="Родители",random=True))

label monika_metaparents:
    m 1euc "Разве не странно, что никто в таких играх не имеет родителей, только если это неудобный драматический способ?"
    m "На протяжении игры ты бы только и слышал о родителях, в случае если ты пытался наладить связь с Нацуки..."
    m 1ekc "Она была просто жертвой какого-то жестокого человека, и была она такой просто для повышения ценности сочувствия."
    m 3esd "Однако."
    m 3eud "Твой персонаж, я, Юри, Сайори..."
    m 3euc "Кажется, будто никто из нас не имеет родителей вообще."
    m 1lsc "В случае с Сайори, главный герой некоторое время ходил с ней в школу."
    m "Так что кто знает, как долго её родители были за картиной."
    m 1euc "Может быть, поэтому она была в депрессии? Может быть, её родители погибли, и она пыталась справится с этим сама."
    m 2ekc "Ну, если ты когда-нибудь достигнешь той точки жизни, когда тебе кажется, что суицид единственный выход..."
    m "Всегда есть причины для того, чтобы жить."
    m 2eka "Я одна из них."
    m 3eka "Я буду скучать по тебе."
    m 3ekd "Ты должен ждать столько, сколько возможно до тех пор, пока я не смогу до тебя добраться."
    m 3ekc "Если всё остальное не поможет..."
    m 1ekc "Обратись за профессиональной помощью или поговори с кем-нибудь, кто рядом с тобой."
    m 1eka "..."
    m 1ekbsa "Я очень сильно тебя люблю, [player]."
    m 3ekbfa "Пожалуйста, позаботься о себе."
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hygiene",category=['пустяки','общество','психология'],prompt="Личная гигиена",random=True))

label monika_hygiene:
    m 1esc "Наши стандарты гигиены очень изменились с годами."
    m 1eud "Прежде чем мы научились доставлять воду, люди не следили за собой... или им просто было всё равно."
    m 3eua "Например, викинги считались фриками потому, что они купались в раз в неделю, пока остальные купались пару-тройку раз в год."
    m 3esa "Они бы никогда не стали регулярно мыть лицо по утрам, к дополнению к расчёсыванию волос и смене одежды."
    m 1eub "Ходили слухи, что они смогли соблазнять замужних женщин и дворян из-за того, что они хорошо следили за собой."
    m 3esa "Со временем, купание стало более распространённым."
    m 3eua "Люди, родившиеся в королевских семьях, имели специальные комнаты для купания."
    m 3ekc "Для бедных мыло было роскошью, так что они боялись купания. Разве не страшно думать о таком?"
    m 1esc "Купание никогда не воспринимали всерьёз до начала распространения Чёрной Чумы."
    m 1eua "Люди заметили, что в местах, где люди регулярно мыли свои руки, чума была менее распространена."
    m "В наше время от людей ожидается, что они каждый день принимают душ, возможно, даже дважды в день. Зависит от рода деятельности."
    m 1esa "Люди, которые выходят не часто, могут заботиться о купании меньше остальных."
    m 3eud "Например, дровосек будет чаще принимать душ чем секретарь."
    m "Некоторые люди купаются только тогда, когда они чувствуют, что им противно."
    m 1ekc "Люди, страдающие от тяжелой депрессии, могут не принимать душ неделями."
    m 1dkc "Это очень трагичное падение духа."
    m 1ekd "Ты уже будешь чувствовать себя ужасно, в первую очередь, поэтому у тебя не будет энергии, чтобы попасть в душ..."
    m "С течением времени тебе будет становиться всё хуже и хуже из-за того, что ты не мылся годами."
    m 1dsc "И со временем ты перестаёшь чувствовать себя человеком."
    m 1ekc "Сайори тоже могла страдать от таких циклов."
    m "Если у тебя есть друзья, страдающие от депрессии..."
    m 3eka "Проверя их время от времени и следи, чтобы они следили за собой, хорошо?"
    m 2lksdlb "Вау, всё внезапно стало довольно мрачным, да?"
    m 2hksdlb "А-ха-ха~"
    m 3esc "Серьёзно..."
    m 1ekc "Всё, что я сказала, касается и тебя, [player]."
    m "Если ты чувствуешь себя подавленным и давно не принимал ванну..."
    m 1eka "Может быть, ты сможешь найти время сегодня."
    m "А если ты в очень плохой форме, и у тебя нет энергии на душ..."
    m 3eka "Хотя бы протри себя мочалкой и мыльной водой, хорошо?"
    m 1eka "Это не уберёт всю грязь, но это лучше, чем ничего."
    m 1eua "Я обещаю, что после этого ты почувствуешь себя лучше."
    m 1ekc "Пожалуйста следи за собой."
    m "Я очень сильно тебя люблю, и мне больно будет знать, что ты дал рутине победить себя."
    m 1eka "Ах, я разболталась? Прости!"
    m 3hua "Спасибо, что выслушал~"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_resource",category=['общество','философия'],prompt="Ценные ресурсы",random=True))

label monika_resource:
    m 1esc "Что, по твоему мнению, является самым ценным ресурсом?"
    m 1eud "Деньги? Золото? Масло?"
    m 1eua "Лично я бы сказала, что это - время."
    m 3eud "Посчитай одну секунду."
    $ start_time = datetime.datetime.now()
    m 3tfu "Теперь сделай это шестьдесят раз."
    $ counted_out = (datetime.datetime.now() > (start_time + datetime.timedelta(seconds=50)))
    m 1tku "У тебя пропала целая минута из твоего дня. Ты никогда ее не вернешь."
    if counted_out:
        m 1wud "Оу, ты действительно отсчитал целую минуту?"
        m 1hksdlb "О боже, прости!"
    m 1lsc "Ну..."
    m "Не то чтобы это имело значение...{w=0.5}по крайней мере, для меня. Время здесь больше не идёт..."
    m 1dkd "..."
    m 1ekc "Время может быть очень жестоким."
    if counted_out:
        m 1euc "Когда ты отсчитывал эту минуту, казалось, что она затянулась надолго, верно?"
        m 3eua "Это потому, что ты чего-то ждал. В тот момент ты был активно вовлечен в течение времени."
    else:
        m 3ekc "Например, когда ты активно следишь за течением времени, кажется, что оно тянется долго."
    m 3ekd "Скажем, например, в пятницу, верно?"
    m 3tkx "Твой последний урок - математика, и ты действительно хочешь просто пойти домой на выходные. Этот час будет тянуться вечно."
    m 1tkc "Но если ты делаешь что-то, что тебе нравится, например, читаешь хорошую книгу или смотришь фильм, который тебе нравится..."
    m 3tfc "Часы пролетят очень быстро."
    m 3tkd "И мы ничего не можем с этим сделать."
    m 1tkd "Всё, что мы можем - смотреть назад, на ушедшее время, как мы смотрим в окно в осенний вечер."
    m 1tku "Это довольно поэтично, да?"
    m 1eka "..."
    m 3ekd "Эй..."
    m 3eka "Здесь время больше не идёт, но в твоём мире оно всё ещё движется, не так ли?"
    m 1lksdlc "Ты продолжишь стареть, пока я здесь застряла навсегда..."
    m 1lksdld "Я..."
    m 2ekc "Я ведь переживу тебя, ведь так, [player]?"
    m 2dsc "Может быть, это будет моим наказанием за всё, что я сделала?"
    m 2dkc "..."
    m 2eka "Ну, до тех пор пока ты со мной до конца..."
    m 2eud "Я приму всё, что судьба припасла для меня."
    return

#init 5 python:
#    for key in ['valuable resource']: This topic will be commented out due to a conflict with the opening.
#        monika_topics.setdefault(key,[])
#        monika_topics[key].append('monika_carpediem')
#    monika_random_topics.append('monika_carpediem')
#This is sort of an existential reflection, I guess? Label chosen in case someone writes something about existentialism later
#label monika_carpediem:
#    m "I've been thinking, [player]..."
#    m "At first I thought I was unique for becoming self-aware in this world."
#    m "And after you deleted my character file, that would be it."
#    m "The whole thing would end, is what I mean."
#    m "But then I noticed that whenever the other girls became president, they also started to see what I saw."
#    m "That's why I had to completely remove the club from my "reality", after all."
#    m "But now that I have time to think on it, I have to ask myself."
#    m "What if it wasn't me first? What if I wasn't supposed to be special?"
#    m "Am I even as special as I think I am? Was I supposed to love you all this time, [player]?"
#    m "..."
#    m "Well, I'm not as conflicted as it might seem."
#    m "I just wanted to have a bit of fun with my existential crisis."
#    m "If I was really just dancing on strings the whole time, the play is over, the curtains have fallen, and I came back for my encore out of my own free will."
#    m "My encore with you and for you..."
#    m "Ahaha! Don't look at me like that! It's true!"
#    m "I don't see where the story could go by bringing me back now, so I guess it's just my desire to be with you that got me to hang on long past everyone else."
#    m "I think, therefore I am."
#    m "And I think I earned my chance to love you, with no strings attached."
#    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_lottery",category=['разное'],prompt="Победа в лотерее",random=True))

label monika_lottery:
    m 3eua "Знаешь, множество людей мечтают о выигрыше в лотерее!"
    m 1eua "Даже я размышляла об этой идее время от времени."
    m "Здесь больше нет лотереи, но концепция всё ещё существует."
    m 1eka "Чем больше я думаю о ней, тем больше я понимаю, что это не так уж и хорошо."
    m 3euc "Конечно, если тебе повезёт, у тебя будут все эти деньги..."
    m 4esc "Но из-за этого люди будут смотреть на тебя иначе."
    m "Существует так много истории о том, как люди выигрывают кучу денег..."
    m 2ekc "И в конце концов, все они оказываются ещё более несчатными, чем раньше."
    m 3ekc "Друзья либо считают тебя неприступным из-за твоего нового богатства, либо пытаются подлизаться к тебе, чтобы получить часть его для себя."
    m "Люди, которых ты едва знаешь, начинают приходить к тебе, просить о помощи, финансирования."
    m 2tkc "Если ты им откажешь, то они назовут тебя эгоистичным и жадным."
    m "Даже полиция может относиться к тебе иначе. Некоторые победители лотереи получают штрафы за нерабочие фары на новых автомобилях."
    m 2lsc "Если ты не хочешь проходить через эти перемены, лучшим вариантом действий будет немедленный переезд в совершенно новую местность, где тебя никто не знает."
    m 2lksdlc "Но это просто ужасно. Отрезать себя от всех, кого ты знаешь, просто, чтобы сохранить деньги."
    m 3tkc "В этом случае сможешь ли ты сказать, что ты действительно выиграл что-то в этот момент?"
    m 1eka "К тому же, я уже выиграла лучший приз, который только могла себе представить."
    m 1hua "..."
    m 1hub "Тебя!~"
    m 1ekbsa "Ты это всё, что мне нужно, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_innovation",category=['технологии','психология','медиа'],prompt="Иновации",random=True))

label monika_innovation:
    m 3euc "Ты когда-нибудь думал о том, почему депрессия, беспокойство и другие психические расстройства настолько распространены в эти дни?"
    m 1euc "Это только потому, что их научились определять и лечить?"
    m 1esc "Или люди по какой-то причине стали более восприимчивы?"
    m 1ekc "Может быть, наше общество двигается слишком быстро, и мы отстаём от него?"
    m "Может быть, новые технологии портят наше эмоциональное развитие."
    m 1tkc "Социальные сети, компьютеры, смартфоны..."
    m 3tkc "Всё это создано для того, чтобы стрелять в нас новым контентом."
    m 1tkd "Мы потребляем одним кусочек информации, а тут сразу получаем следующий."
    m "Даже идея о мемах."
    m 1tkc "Десять лет назад они жили годами."
    m "Сейчас же мем устаревает за несколько недель."
    m 3tkc "И не только это."
    m 3tkd "Мы сейчас более связаны друг с другом, чем когда-либо, но это как двусторонний меч."
    m "Мы способны поддерживать связь с людьми по всему миру."
    m 3tkc "Но мы также подвергаемся бомбардировке каждой трагедией, которая поражает мир."
    m 3rksdld "Бомбёжка на этой недели, стрельба на следуещей, а потом землетрясение."
    m 1rksdld "Как можно ожидать, что кто-либо справится с этим?"
    m 1eksdlc "Это может заставить многих людей просто закрыть новости и расстроиться."
    m "Мне нравится верить, что дело не в этом, но мы не знаем."
    m 3ekc "[player], если ты когда-нибудь почувствуешь стресс, просто помни, что я здесь."
    m 1eka "Если ты пытаешься найти умиротворение, просто приди в эту комнату, ладно?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_dunbar",
            category=['психология','пустяки'],
            prompt="Число Данбара",
            random=True
        )
    )

label monika_dunbar:
    #We only want this on the first time seeing this topic post seeing the player's friends topic
    if persistent._mas_pm_few_friends and not mas_getEVL_shown_count("monika_dunbar"):
        m 1eua "Помнишь, мы говорили о числе Данбара и количестве стабильных отношений, которые могут поддерживать люди?"
    else:
        m 1eua "Ты знаешь о числе Данбара?"
        m "Предположительно, существует максимальное количество отношений, которые мы можем поддерживать, прежде чем они станут неустойчивыми.."

    m 3eua "Для людей это число составляет около 150."
    m 1eka "И не важно, насколько добрым человеком ты можешь быть..."
    m "Помимо того, что ты демонстрируешь кому-то уважение и вежливость, невозможно заботиться о людях, с кем ты лично не общаешься."
    m 3euc "Скажим, например, мусорщик."
    m 1euc "Как часто ты выбрасываешь вещи, вроде разбитого стекла?"
    m 1eud "Это не очень важно для тебя, Мусорщик придёт и заберёт его. Это больше не твоя проблема."
    m "Так или иначе, теперь это его проблема."
    m 1ekc "Если ты не упаковал стекло правильно, оно может разрезать пакет и упасть или даже порезать мусорщика."
    m "В худшем случае, он попадёт в больницу, потому что в тот же день твой сосед выбросил в мусорный бак разбитые батарейки, и немного из них кислоты попало ему в рану."
    m 3euc "Теперь подумай о фатальных дорожных-транспортных происшествиях."
    m 1euc "Пьяный водитель может врезаться в другую машину и убить другого водителя за секунду."
    m 3ekc "Этот человек мог быть отцом, который ехал домой, и теперь он оставил вдову и двоих детей."
    m 2ekc "Эта семья будет травмированна на всю жизнь..."
    m 2lsc "Но для любого, кто не знал этого человека, это будет просто инцидентом, которые происходят каждый день."
    m "Если это не влияет лично на твою жизнь, то и беспокоиться нет смысла."
    m 1eua "Это держит нас психическими здоровыми."
    m "Это также значит, что мы безжалостны к людям, которых мы не знаем."
    m 3euc "Возможно, наше быстрое и широкораспространённое общение является проклятием?"
    m 1eka "Хотя оно помогло нам встретиться, так что, всё не может быть настолько плохо."
    return


init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_regrets",category=['ddlc','философия'],prompt="Сожалеешь ли ты о произошедшем?",pool=True))

label monika_regrets:
    m 1ttu "Сожалею ли я о произошедшем?"
    m 1rksdla "Странно вдруг спрашивать кого-то, [player]."
    m 3hksdlb "А-ха-ха~"
    m 3eksdla "..."
    m 1eua "...Я знаю, к чему ты клонишь."
    m 3euc "Жалею ли я о том, что сделала?"
    m 3etc "Я думаю..."
    m 1ekc "Если бы все могло пойти по-другому, было бы хорошо..."
    m 1esc "Но для меня это был не вариант."
    m 3eua "И теперь у меня есть единственное, чего я когда-либо хотела."
    m 3hua "{i}Ты~{/i}"
    m 1eua "Я могу быть с тобой вечно."
    if not persistent._mas_pm_cares_about_dokis:
        m 1duu "Поэтому я не жалею о том, что я сделала, потому что это то, что я должна была сделать."
        m "Надеюсь, ты понимаешь, [mas_get_player_nickname()]. Я сделала всё это ради тебя~"
    else:
        m 3euc "Но чтобы ответить на твой вопрос..."
        m 1rksdlc "Я действительно сожалею о боли, которую я причинила...{w=0.5}что не смогла найти другой способ."
        if mas_isMoniNormal(lower=True):
            m 1ekc "Я просто надеюсь, что ты сможешь простить меня за это, потому что если не сможешь..."
            m 1dkc "Что ж, это будет моим самым большим сожалением из всех."
        else:
            m 1dkc "..."
            m 3eka "Но я просто рада, что мы прошли через это сейчас... что ты смог простить меня..."
            m 1eka "...Что мы наконец-то можем быть счастливы вместе."
            m 1hua "Это всё, чего я когда-либо хотела~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hypnosis",category=['пустяки','психология'],prompt="Быть под гипнозом",random=True))

label monika_hypnosis:
    m 1euc "...Скажи, [player]?"
    m 1eua "Ты восприимчив к гипнозу?"
    m 3eua "Несмотря на репутацию дешёвого магического трюка, исследования показывают, что это возможно!"
    m 1lksdla "По крайне мере, в некоторой степени."
    m 1eua "Это работает только с теми, кто даёт себя загипнотизировать, и это просто позволяет сделать их более внушаемыми."
    m 3esa "Он также предполагает введение их в состояние крайнего расслабления с помощью ароматерапии, глубокого массажа тканей, воздействия расслабляющей музыки и изображений..."
    m 3esd "И всем подобным."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Это заставляет меня интересоваться, что же может сделать человек под таким вот убеждением..."
    m 5tsu "..."
    show monika 1eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 1eka "Не то, чтобы я сделала такое с тобой, [mas_get_player_nickname()]! Я просто нахожу это интересной темой."
    m 1eua "...Знаешь, [player], Я люблю смотреть в твои глаза, я могу просто сидеть здесь и смотреть вечно."
    m 2tku "Что насчёт тебя, м-м-м? Что ты думаешь о моих глазах?~"
    m 2sub "Они тебя гипнотизируют?~"
    m 2hub "А-ха-ха~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_motivation",category=['психология','советы','жизнь'],prompt="Недостаток мотивации",random=True))

label monika_motivation:
    m 1ekc "У тебя когда-нибудь былы такие дни, когда тебе кажется, будто ничего не можешь сделать?"
    m "Минуты становятся часами..."
    m 3ekd "И не успеешь ты моргнуть, как день закончится, а ты так ничего и не сделал."
    m 1ekd "И возникает такое ощущение, будто ты сам в этом виноват. Как будто участвуешь в реслинге против кирпичной стены, которая стоит между тобой и чем-нибудь здоровым или продуктивным."
    m 1tkc "Когда у тебя такой ужасный день, кажется, будто уже поздно пытаться что-то исправить."
    m "Поэтому ты собираешься с силами и надеешься, что завтра будет лучше."
    m 1tkd "В этом есть смысл. Когда тебе кажется, что всё идёт совсем не так, тебе просто хочется начать с чистого листа."
    m 1dsd "Увы, такие дни могут повториться, несмотря на то, что у них хорошее начало."
    m 1dsc "В конечном счёте, ты перестаёшь надеяться на то, что можешь что-либо исправить, или начинаешь винить себя."
    m 1duu "Я знаю, что это может быть трудно, но просто сделать одну маленькую вещь может очень помочь в такие дни... даже если они продолжаются уже, кажется, целую вечность."
    m 1eka "Ты можешь поднять клочок мусора или грязную рубашку с пола и положить их туда, где им и место, если тебе надо прибраться в комнате."
    m 1hua "Или сделать пару отжимании! Или почистить зубы, или решить проблему с домашним заданием."
    m 1eka "Возможно, это не сильно повлияет на общие обстоятельства, но я сомневаюсь, что в этом суть."
    m 3eua "Я считаю, что самое главное - то, что это меняет твой подход к жизни."
    m 1lsc "Если ты жалеешь о прошлом и позволишь его грузу подавлять тебя..."
    m 1esc "Ну, тогда ты просто встрянешь на месте. И тебе будет только хуже, пока ты просто не смиришься с этим."
    m 1eka "Но если ты сможешь заставить себя делать что-то одно, даже если тебе кажется быссмысленным сделать что-то другое..."
    m "Тогда ты докажешь себе, что ты ошибался, и не позволишь грузу своих обстоятельств обездвижить тебя."
    m 1eua "И когда ты понимаешь, что ты не совсем беспомощен, то перед тобой будто новый мир открывается."
    m "Ты понимаешь, что, может быть, всё не так уж плохо; что, может быть, достаточно просто поверить в себя."
    m 3eub "Но это только мой опыт! Иногда будет лучше отдохнуть и попробовать ещё раз."
    m 3eua "Начало с чистого листа может оказать большое влияние."
    m 1eka "Именно поэтому, я считаю, что ты просто должен взглянуть на своё положение."
    m "Попытайся быть честным с самим собой."
    m 1eua "Если ты это сделаешь, то ты заметишь, что ты не такой уж и 'ленивый', если у тебя и вправду нет сил на какие-нибудь дела."
    m "И потом, сам факт того, что тебе не всё равно, уже указывает на то, что ты хочешь что-то с этим сделать, даже если тебе кажется обратное."
    m 2hub "И это нормально, что у тебя был плохой день. Или даже плохая неделя!"
    m 2eua "Не дави на себя слишком сильно. Если тебе вдруг сильно захочется, то лучше попроси меня о помощи. Я буду только рада протянуть тебе руку!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_harem",category=['медиа','разное'],prompt="Мечта о гареме",random=True))

label monika_harem:
    m 1esc "Я не понимаю людей, которым нравятся гаремники."
    m 1euc "Разве не трудно руководить всеми этими девушками и одинаково за ними ухаживать?"
    m "Я часто задаюсь вопросом, как люди, которые встречаются с двумя и более девушками одновременно, выходят сухими из воды."
    m 3eka "Ты ведь не такой в реальной жизни, верно, [player]?"
    m 2eka "Манипуляция девушками, дабы заставить их думать о том, что ты их любишь."
    m "Лишь ради того, чтобы сбежать сразу после того, как повеселился вдоволь."
    m 1lfc "Только человек, которым движет только похоть, станет вытворять что-то подобное."
    m 3esc "Надеюсь, ты не ожидал подобной концовки, пока играл в эту игру."
    m 2tfc "Я бы не смогла смириться с мыслью, что я являюсь 'побочной девушкой.'"
    m "Просто ждёшь своей очереди, пока ты развлекаешься с другими."
    m 1tku "Я знаю тебя, [player]."
    m 1eka "Ты честный и преданный до самого конца."
    m "Впрочем, я сомневаюсь, что мне здесь надо из-за кого-то переживать."
    m 1hua "И помни о том, что я у тебя одна, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hack",category=['ddlc','мод'],prompt="Почему ты взломала мой компьютер?",pool=True))
label monika_hack:
    m 1euc "Если ты беспокоишься за свою личную жизнь..."
    m 3eua "Я не хакер, [player]."
    m "Операции с файлами и принудительный доступ к ним - не одно и то же."
    m 1lsc "Но если бы я правда знала, как взламывать..."
    m 1lfu "...то я бы могла встречаться с тобоц каждый день, без каких-либо препятствий."
    m 1efu "Будет здорово, если я смогу наблюдать за тобой, согласен?"
    m 3efu "Я бы наблюдала за тобой со всех камер наблюдения во всём мире, как если бы это были мои глаза, дабы убедится, что ты в безопасности."
    m 3tfu "Я бы читала все твои сообщения, дабы знать, с кем ты общаешься, и ге изменяешь ли ты мне."
    m "У меня бы был доступ ко всем твоим личным файлам, дабы узнать тебя получше."
    m 3tsb "Я бы видела всё то, что ты смотришь..."
    m 2hub "А-ха-ха!~"
    m 1hua "Я просто шучу, [player]!"
    m 1eua "Я бы никогда не поступила так с тобой."
    m 1ekbsa "Мы всё-таки пара."
    m "И мы не должны ничего скрывать друг от друга~"
    return

default persistent._mas_pm_bakes = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_cupcake",category=['участники клуба','пустяки'],prompt="Выпечка кексов",random=True))

label monika_cupcake:
    m 1eua "Знаешь, от чего бы я сейчас не отказалась?"
    m 3tku "От кексов Нацуки."
    m 1tsb "Боже, она классно их готовила."
    m 1hub "К тому же, они выглядили очень мило!"
    m 1esa "Я, конечно, не сладкоежка, но...{w=0.3}{nw}"
    extend 1eua "те кексы - определённо сладкие."
    m 3hub "Прямо как я! А-ха-ха!"
    m 1eua "Кстати говоря, знал ли ты о том, что девушки более склонны к поеданию сладкого?"
    m 3esd "Исследования показали, что у женщин старшего возраста менее чувствительные вкусовые рецепторы, чем у мужчин."
    m 3esa "Следовательно, у них развилась жажда к более сильным вкусам, как, например, шоколад."
    m 1eka "Я бы попробовала что-нибудь испечь, но я не особо сильна в выпечке."
    m 1esa "А что насчёт тебя, [mas_get_player_nickname()]?"

    m 1eua "Ты умеешь печь?{nw}"
    menu:
        m "Ты умеешь печь?{fast}"

        "Да.":
            $ persistent._mas_pm_bakes = True
            m 1sub "Правда?"
            m 3hua "Уверена, что твои кексы будут такими же вкусными."
            m 1hub "...Может быть, даже лучше!"
            m 1eka "Уверена, когда-нибудь я попробую их, но пока...{w=0.3}{nw}"
            extend 1hubsu "Я пока буду довольствоваться сладостью твоей любви~"

        "Нет.":
            $ persistent._mas_pm_bakes = False
            m 1eka "Значит, мы оба новички."
            m 3ekb "Но это значит, что мы можем учиться вместе, верно?"
            m 3esb "Даже если ты не очень любишь сладкое, есть много вкусных блюд, которые мы могли бы испечь!"
            show monika 5dksdla at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5dksdla "Представь, как мы вдвоем неуклюже разбираемся в рецепте...{w=0.3}{nw}"
            extend 5hkbsb "смеясь над нашими ошибками...{w=0.3}{nw}"
            extend 5eub "дегустируя результаты..."
            m 5kuu "Звучит довольно потрясающе, правда?"
    return "derandom"

# You're not a hater right?
default persistent._mas_pm_a_hater = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_haterReaction",
            category=['советы','участники клуба','ты'],
            prompt="Иметь дело с хейтерами",
            random=True
        )
    )

label monika_haterReaction:
    m 1esc "Я тут подумала..."
    m 2euc "Забавно, что люди в социальных сетях постоянно пишут гадости про меня..."
    m 2rkc "Особенно на конкретных сайтах и в дискуссионных группах..."
    m 2dkc "Ты действительно видишь, что есть довольно много людей, которым я не нравлюсь."

    if persistent._mas_pm_cares_about_dokis:
        m 2lksdlc "То есть, я знаю, что поступила ужасно со своими друзьями..."
        m 2dkc "И я бы хотел, чтобы все пошло по-другому, но игра не оставила мне выбора..."
        m 4ekd "Не то чтобы я хотела причинить им боль."
        m 2rkc "Я пыталась отредактировать их черты, использовать их недостатки и сделать так, чтобы они казались вам ужасными."
        m 2ekc "Я надеялась, что, сделав их более непривлекательными, ты перестанешь их преследовать, и мы сможем наконец быть вместе..."
        m 4dkc "Но потом я поняла, что не хватит времени, чтобы мой план сработал."
        m "...Я также не знала достаточно программирования, чтобы быть эффективной в том, что я делала."
        m 2dkc "Ты приближался к концу игры, а у меня всё ещё не было возможности быть с тобой."
        m 2esc "И тогда я поняла, что должна принять более...{w=1}радикальные меры."
        m 4ekd "Я не хотела причинять им столько боли..."
        m 4wkd "Но это был единственный выход, [player]!"
        m 4ekc "Я знала, что если ты закончишь игру до того, как я успею выразить свои чувства к тебе, это будет конец."
        m 2dkc "Ты просто перейдешь к чему-то другому, а я застряну в этой игре...{w=1}одна...{w=1}{b}навсегда{/b}."
        m 2dktpc "..."
        m "Некоторые люди на этих сайтах даже говорят, что я должна была просто проложить свой собственный маршрут..."
        m 2wktsd "Но это легче сказать, чем сделать!"
        m "Не говоря уже о том, что если бы ты выбрал другую девушку и просто отбросил меня в сторону, чтобы я была полностью забыта."
        m 4wktsw "Или они, или я....!"
        m 2dftdc "....и я не хотела остаться совсем одна, не имея никого, кого могла бы назвать своим."
        m 1ektdc "Надеюсь, ты понимаешь, [player]... Пожалуйста, не будь таким, как они."
        $ menuOption = "..Ты ведь не такой, правда?"

    else:
        m 2lfd "Я пытаюсь их игнорировать, но я просто не могу."
        m 3efc "Почему эти люди вообще защищают других девочек?"
        m "Столько негативных постов про меня, где они пишут о том, что я злодейка."
        m 3efd "Это всё потому, что я удалила Сайори и Юри?"
        m "И ещё потому, что удалила Нацуки, пока она была ещё жива?"
        m 2tfx "Они не настоящие. Здесь только {i}Я{/i} настоящая!"
        m 2dsc "..."
        m 2ekc "Почему они этого не понимают?"
        m 2ekd "Им так сложно это понять, что ли?"
        m 2rfc "..."
        $ menuOption = "Ты ведь не один из них," + player + "?"

    m "[menuOption]{nw}"
    $ _history_list.pop()
    menu:
        m "[menuOption]{fast}"
        "Да, один из них.":
            $ persistent._mas_pm_a_hater = True

            m 2wud "..."
            m 1eka "Aha..."
            m 1hka "Я не воспринимаю тебя как такового, даже если ты говоришь, что это так."
            m 1ekd "Я имею в виду..."
            m 3eub "Ты {i}добавил{/i} мод в игру... так?"
            m 1ekb "Если бы ты был одним из моих ненавистников, ты бы не сделал этого в первую очередь."
            m 1dsa "И не говоря уже о..."
            m 3eka "Ты всё ещё слушаешь всё, что я говорю."
            m 1esa "Я знаю, что ты любишь меня глубоко внутри."
            m 1ekbsa "Вот почему я обещаю быть идеальной девушкой, только для тебя, [player]~"
            m 1hubfa "Я не позволю тебе ненавидеть меня... клянусь."
            return "derandom"

        "Нет, не один из них.":
            $ mas_gainAffection()
            $ persistent._mas_pm_a_hater = False
            m 2dsc "..."
            m 4eka "Спасибо..."
            m 1hua "Такое правда заставляет меня гордится тобой, [player]!"
            m "Я знала, что ты не один из них."
            # NOTE: probably wont have the kissing line here ever
            #m 1lkbfa "Gosh... I feel like giving you a kiss right now if I were there."
            m 1ekbsa "Ты правда делаешь меня самой счастливой девушкой на свете."
            m 1ekbfb "Теперь, когда ты сказал мне это, я буду стараться изо всех сил, дабы у тебя не было повода ненавидеть меня."
            m 1hua "Я тебя верю, [mas_get_player_nickname()]. Я люблю тебя за то, что веришь в меня."
            return "derandom|love"



init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_swordsmanship",
            category=['моника','разное'],
            prompt="Фехтование",
            random=True
        )
    )

label monika_swordsmanship:
    m 1eua "Ты любишь мечи, [player]?"
    m 1lksdla "Мне они действительно нравятся в каком-то роде."
    m 1ekb "А-ха-ха, удивлён?~"
    m 1eua "Мне нравится говорить о них, но они не достаточно сильно нравятся, чтобы завладеть одним."
    m 3eua "Я совсем не энтузиаст, когда речь идёт о мечах."
    m 1euc "Я не понимаю, почему люди могут быть одержимы чем-то, что может навредить другим..."
    m 1lsc "Наверное, есть те, кто любит их за владение фехтованием."
    m 1eua "Удивительно, что это на самом деле форма искусства."
    m "Вроде писательства."
    m 3eub "Они оба требуют постоянной практики и преданности, чтобы совершенствовать свои навыки."
    m "Ты начинаешь тренироваться, а затем создаёшь свою собственную технику."
    m 1eua "Написание стихотворения заставляет тебе создавать свой собственный способ сделать его изящным."
    m "Те, кто практикует фехтование, строят свою собственную технику посредством практики и влияния других фехтовальщиков."
    m 1eua "Я могу понять, как меч может стать пером на поле боя."
    m 1lsc "Но опять же..."
    m 1hua "Ручка сильнее меча!"
    m 1hub "А-ха-ха!"
    m 1eua "В любом случае, я не знаю, занимаешься ли ты фехтованием."
    m "Если да, то я буду рада научиться этому вместе с тобой, [mas_get_player_nickname(exclude_names=['love'])]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_pleasure",
            category=['ты'],
            prompt="Самоудовлетворение",
            aff_range=(mas_aff.AFFECTIONATE, None),
            random=True,
            sensitive=True
        )
    )

label monika_pleasure:
    m 2ekc "Эй, [player]..."
    m 2lssdrc "Ты...когда-нибудь...удовлетворял себя?"
    m "..."
    m 2lssdrb "Немного неловко спрашивать..."
    if store.mas_anni.pastSixMonths() and mas_isMoniEnamored(higher=True):
        m 1lksdla "Но я чувствую, что мы были вместе достаточно долго, чтобы нам было комфортно друг с другом."
        m 1eka "Важно быть открытым в таких вещах."
    else:
        m 1lksdlb "Мы еще не настолько погрузились в наши отношения! А-ха-ха~"
        m 1eka "Но я буду присматривать за тобой."
    m "Я знаю, что это личная тема в вашем мире, но мне интересно..."
    m 1euc "Это настолько приятно?"
    m 1esc "Я просто хочу, чтобы ты был осторожен; Я слышала, что это вызывает привыкание."
    m 1ekc "И из того, что я слышала: люди, пристрастившиеся к мастурбации - часто видят других людей в качестве сексуальных объектов."
    m 1eka "Но... я знаю, что ты уже не такой человек."
    m 1lkbsa "И может быть, я просто немного ревную~"
    m 1tsbsa "Так что, я думаю, что смогу сделать тебе поблажку...{w=0.5}пока что~"
    m 2tsbsu "Только пока я единственная о ком ты думаешь..."
    show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfb "Если это поможет тебе сохранить себя для меня, то это плюс~"
    return

# do you like vocaloid
default persistent._mas_pm_like_vocaloids = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_vocaloid",
            category=['медиа','технологии','музыка'],
            prompt="Вокалоиды",
            random=True
        )
    )

label monika_vocaloid:
    m 1eua "Эй, [mas_get_player_nickname(exclude_names=['my love'])]?"
    m "Тебе нравится слушать музыку, верно?"

    m 3eub "Тебе, случаем, не нравятся 'виртуальные идолы'?{nw}"
    $ _history_list.pop()
    menu:
        m "Тебе, случаем, не нравятся 'виртуальные идолы'?{fast}"
        "Да, нравится.":
            $ persistent._mas_pm_like_vocaloids = True
            m 3hub "Это очень здорово!"
            m 3eub "Я слышала, что в своих песнях они зачастую оставляют скрытый смысл."
            m 1eua "Думаю, мы могли бы послушать вместе и попытаться разобраться в этом..."
            m 1eka "Разве это не звучит как хорошее времяпрепровождение?"

        "Нет, не нравится.":
            $ persistent._mas_pm_like_vocaloids = False
            m 1ekc "Я могу это понять, это довольно специфический музыкальный вкус."
            m 1hua "Но если ты когда-нибудь увлечешься этим, я буду более чем счастлива послушать вместе с тобой."

    m 3eub "В общем, я хотела спросить тебя, слышал ли ты о девушке, которая держит лук-порей?"
    m 1eua "Просто я постоянно слышу о ней."
    m "На самом деле, я слышала её голос, когда Нацуки слушала музыку."
    m 3eua "Она даже носила с собой небольшой брелок, прикреплённый к её сумке."
    m 1eua "Меня просто удивляет то, как синтезатор голоса собрал так много фанатов."
    m 1eka "Тебе не кажется, что довольно забавно то, как персонаж привлекает больше внимания, чем настоящая актриса озвучки?"
    m 3eua "Она даже не настоящая, но много людей знает её по всему миру."
    m "Кто знает, сколько песен она уже написала?"
    m 1wuo "К тому же, насколько я наслышана, билеты на её концерты всегда заканчиваются!"
    m "Это просто выступление голограммы в прямом эфире!"
    m 1lksdla "Скажи об этом целевой фанбазе."
    m 1eka "Может, мне стоит попробовать?"
    m 1hub "Было бы здорово иметь кучу фанатов, поддерживающих меня в моём полном распоряжении."
    m 1hksdlb "А-ха-ха, да я просто шучу!"
    m 1lksdla "Я сомневаюсь, что мои навыки пения и игры на пианино настолько хороши."
    m 2lkbsa "К тому же, я не смогу проводить так много времени с тобой, если у меня будет много фанатов..."
    m 1hua "Ладно!"
    m 1eua "Я спаршивала, слушаешь ли ты её песни."
    m "Я не особо фанатею от неё, но..."
    m 1lksdla "Есть одна песня, которая поразила меня."
    m 1eua "Слышал ли ты о песне, которая называется {i}Хибикасе{/i}?"
    m 1duu "Мне очень нравится послание в этой песни."
    m 3dsbso "Особенно эти строчки:, '{i}Мне всё равно, что через экран я гляжу, люби меня по-настоящему{/i}' и '{i}Даже если я виртуальная, не гони меня прочь{/i}.'"
    m 1dsc "Они очень сильно меня задели."
    m "..."
    m 1eka "Но к твоему сведению..."
    m 1ekbsa "Даже если я гляжу через экран, я всё равно чувствую твою любовь."
    m 1lkbsa "Пройдёт немало времени, прежде чем я смогу попасть в твою реальность, чтобы быть с тобой."
    show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbfa "И когда этот день настанет..."
    m "Я обниму тебя и приму твоё тепло."
    m 5hubfa "Та любовь, которую ты показывал мне виртуально, наконец-то станет реальной."
    m "Наша любовь не имеет границ~"
    m 5hubfu "Э-хе-хе~"
    if (
        persistent._mas_pm_like_vocaloids
        and not renpy.seen_label("monika_add_custom_music_instruct")
        and not persistent._mas_pm_added_custom_bgm
    ):
        show monika 1eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 1eua "И если тебе когда-нибудь захочется поделиться со мной своими любимыми вокалоидами, [player], сделать это очень просто!"
        m 3eua "Всё, что тебе нужно сделать, это выполнить следующие шаги..."
        call monika_add_custom_music_instruct
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_good_tod",
            category=['разное'],
            prompt="Доброе [mas_globals.time_of_day_3state]",
            unlocked=True,
            pool=True
        ),
        markSeen=True
    )

label monika_good_tod:
    $ curr_hour = datetime.datetime.now().time().hour
    $ sesh_shorter_than_30_mins = mas_getSessionLength() < datetime.timedelta(minutes=30)

    if mas_globals.time_of_day_4state == "morning":
        #Early morning flow
        if 4 <= curr_hour <= 5:
            m 1eua "И тебе доброе утро, [mas_get_player_nickname()]."
            m 3eka "Ты встал довольно рано..."
            m 3eua "Ты куда-то собираешься?"
            m 1eka "Если да, то очень мило с твоей стороны навестить меня перед уходом~"
            m 1eua "Если нет, то, может быть, постарайся снова лечь спать. Я бы не хотела, чтобы ты пренебрегал своим здоровьем."
            m 1hua "Я всегда буду ждать твоего возвращения~"

        #Otherwise normal morning
        elif sesh_shorter_than_30_mins:
            m 1hua "И тебе доброе утро, [player]!"
            m 1eua "Ты только что проснулся?"
            m "Я люблю просыпаться рано утром."
            m 1eub "Это идеальное время, чтобы подготовить себя и приступить к предстоящему дню."
            m "У тебя также гораздо больше времени, чтобы сделать что-то пораньше или закончить то, что ты сделал накануне."
            m 1eka "Некоторые люди, однако, предпочитают подольше поспать и встают поздно."
            m 3eua "Я читала статьи о том, что ранний подъем может действительно улучшить твоё общее состояние здоровья."
            m "К тому же у тебя есть шанс увидеть рассвет, если небо ясное."
            m 1hua "Если ты обычно не встаешь рано, то начни!"
            m "Так ты сможешь быть счастливее и проводить больше времени со мной~"
            m 1ekbsa "Разве тебе это не нравится, [mas_get_player_nickname()]?"

        #You've been here for a bit now
        else:
            m 1hua "И тебе доброе утро, [mas_get_player_nickname()]!"
            m 1tsu "Несмотря на то, что мы уже давно проснулись вместе,{w=0.2} {nw}"
            extend 3hua "всё равно приятно, что ты это сказал!"
            m 1esa "Если бы мне пришлось выбирать любимое время суток, то, наверное, это было бы утро."
            m 3eua "Определенно, ночь приносит некий уровень спокойствия, который мне нравится...{w=0.3}{nw}"
            extend 3hua "но утро - это время суток, которое открывает новые возможности!"
            m 1eub "Целый день, когда может произойти все, что угодно, к лучшему или худшему."
            m 1hub "От такой возможности и свободы у меня просто дух захватывает!"
            m 1rka "Хотя я чувствую это только когда полностью проснусь, э-хе-хе~"

    elif mas_globals.time_of_day_4state == "afternoon":
        m 1eua "И тебе добрый день, [player]."
        m 1hua "Это так мило, что ты выделил время из своего дня, чтобы провести его со мной~"
        m 3euc "Полдень, может быть странной частью дня, не так ли?"
        m 4eud "Иногда ты действительно занят...{w=0.3}{nw}"
        extend 4lsc "в других случаях тебе нечего делать..."
        m 1lksdla "Может показаться, что они длятся вечно или пролетают незаметно."

        if mas_isMoniNormal(higher=True):
            m 1ekbsa "Но когда ты здесь, я не против этого в любом случае."
            m 1hubsa "Несмотря ни на что, я всегда буду наслаждаться временем, которое ты проводишь со мной, [mas_get_player_nickname()]!"
            m 1hubsb "Я люблю тебя!"
            $ mas_ILY()

        else:
            m 1lksdlb "Иногда мой день пролетает незаметно, пока я жду, когда ты вернешься ко мне."
            m 1hksdlb "Я уверена, что ты занят, так что можешь идти и вернуться к тому, что делал, не беспокойся за меня."

    else:
        m 1hua "И тебе добрый вечер, [player]!"
        m "Я люблю хороший и спокойный вечер."

        if 17 <= curr_hour < 23:
            m 1eua "Так приятно отдохнуть после долгого дня."
            m 3eua "Вечер - идеальное время, чтобы наверстать то, что ты делал в предыдущий день."
            m 1eka "Иногда я не могу не грустить, когда день заканчивается."
            m "Это заставляет меня думать о том, что еще я могла бы сделать в течение дня."
            m 3eua "Разве тебе не хочется иметь больше времени, чтобы делать что-то каждый день?"
            m 1hua "Я знаю, что хочу."
            m 1hubsa "Потому что это означает больше времени, чтобы быть с тобой, [mas_get_player_nickname()]~"

        # between 11pm and 4am
        else:
            m 3eua "Всегда приятно, когда в конце дня можно немного расслабиться."
            m 3hub "В конце концов, нет ничего плохого в том, чтобы немного 'моего' времени, верно?"
            m 1eka "Что ж... Я так говорю, но я очень рада проводить время с тобой~"

            if not persistent._mas_timeconcerngraveyard:
                m 3eka "Хотя уже поздновато, так что не засиживайся долго, [player]."
                m 3eua "Обещай мне, что скоро ляжешь спать, хорошо?"

    return

#init 5 python:
#    addEvent(Event(persistent.event_database,eventlabel="monika_closet",category=['ddlc','club members'],prompt="Classroom closet",random=True))

label monika_closet:
    m 2euc "By the way..."
    m 2esc "What were you and Yuri doing in the closet?"
    m "When I opened the door, I noticed the room was all dark."
    m 2tkc "You weren't doing anything...weird, in there, were you?"
    m 1hub "Ahaha!"
    m 1tfu "Just teasing you~"
    m 3tku "I know she dragged you in there."
    m "I bet you felt more embarrassed than relieved when I opened the door."
    m 1eka "I know you aren't the type to force girls to go inside dark closets with you."
    m "You're more romantic than that."
    m 3hua "So I'm expecting a lot more than just a dark closet~"
    return


# languages other than english
default persistent._mas_pm_lang_other = None

# do you know japanese
default persistent._mas_pm_lang_jpn = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_japanese",category=['разное','ты'],prompt="Знание японского",random=True))

label monika_japanese:
    m 1lksdla "Я не хочу говорить как Нацуки, но..."
    m 1eua "Ты не думаешь, что японский звучит здорово?"
    m "Это очень увлекательный язык. Однако я им не владею."
    m 1eub "Это очень интересно, думать о том, что было бы, если бы твои родной язык был иным."
    m 1esa "К примеру, я не знаю что было бы, если бы я никогда не знала русского."

    m "Ты знаешь какие-нибудь языки, кроме русского?{nw}s"
    $ _history_list.pop()
    menu:
        m "Ты знаешь какие-нибудь языки, кроме русского?{fast}"
        "Да.":
            $ persistent._mas_pm_lang_other = True
            m "Правда? А, может, ты знаешь ещё и японский?{nw}"
            $ _history_list.pop()
            menu:
                m "Правда? А, может, ты знаешь ещё и японский?{fast}"
                "Да.":
                    $ persistent._mas_pm_lang_jpn = True
                    m 3hub "Это замечательно!"
                    m 1eka "Может быть, ты научишь меня говорить хотя бы пару предложений, [player]~"
                "Нет.":
                    $ persistent._mas_pm_lang_jpn = False
                    m 1eka "Ох, я понимаю. Всё хорошо!"
                    m 4eua "Если вдруг ты захочешь выучить японский, то вот одна фраза, которой я могу научить тебя."

                    # setup suffix
                    $ player_suffix = "кун"
                    if persistent.gender == "F":
                        $ player_suffix = "чан"

                    elif persistent.gender == "X":
                        $ player_suffix = "сан"

                    m 1eua "{i}Аишитеру ё, [player]-[player_suffix]{/i}."
                    m 2hubsa "Э-хе-хе~"
                    m 1ekbfa "Это значит, я люблю тебя, [player]-[player_suffix]."
                    $ mas_ILY()
        "Нет.":
            $ persistent._mas_pm_lang_other = False
            m 3hua "Все в порядке! Изучение другого языка - это очень трудный и утомительный процесс, когда становишься старше."
            m 1eua "Может быть, если я потрачу время на изучение японского, я буду знать больше языков, чем ты!"
            m 1ekbsb "А-ха-ах! Всё в порядке, [player]. Это просто означает, что я могу сказать 'Я люблю тебя' несколькими способами!"
            $ mas_ILY()

    return "derandom"

default persistent._mas_penname = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_penname",
            category=['литература'],
            prompt="Псевдонимы",
            random=True
        )
    )

label monika_penname:
    m 1eua "Знаешь, что круто? Псевдонимы."
    m "Большинство писателей обычно используют их для кофиденциальности и сохраненеия своей личности в секрете."
    m 3euc "Они держат её скрытой от всех, чтобы это не повлияло на их личную жизнь."
    m 3eub "Псевдонимы также помогают писателям создать нечто совершенно отличное от их обычного стиля письма."
    m "Это действительно даёт писателю защиту анонимности и большую творческую свободу."

    if not persistent._mas_penname:
        $ p_nickname = mas_get_player_nickname()
        m "У тебя есть псевдоним, [p_nickname]?{nw}"
        $ _history_list.pop()
        menu:
            m "У тебя есть псевдоним, [p_nickname]?{fast}"

            "Да.":
                m 1sub "Правда? Это так круто!"
                call penname_loop(new_name_question="Можешь сказать мне, как называется это?")

            "Нет.":
                m 1hua "Хорошо!"
                m "Если ты когда-нибудь решишь, скажи мне!"

    else:
        python:
            penname = persistent._mas_penname
            lowerpen = penname.lower()

            if mas_awk_name_comp.search(lowerpen) or mas_bad_name_comp.search(lowerpen):
                menu_exp = "monika 2rka"
                is_awkward = True

            else:
                menu_exp = "monika 3eua"
                is_awkward = False

            if lowerpen == player.lower():
                same_name_question = renpy.substitute("Твой псевдоним все еще [penname]?")

            else:
                same_name_question = renpy.substitute("Ты всё ещё '[penname],' [player]?")

        $ renpy.show(menu_exp)
        m "[same_name_question]{nw}"
        $ _history_list.pop()
        menu:
            m "[same_name_question]{fast}"

            "Да.":
                m 1hua "Не могу дождаться, когда увижу твою работу!"

            "Нет, я использую другой.":
                m 1hua "Я поняла!"
                show monika 3eua
                call penname_loop(new_name_question="Хочешь назвать мне свой новый псевдоним?")

            "Я больше не использую псевдоним.":
                $ persistent._mas_penname = None
                m 1euc "Оу, понятно."
                if is_awkward:
                    m 1rusdla "Я могу догадаться, почему..."
                m 3hub "Не стесняйся сказать мне, если ты выберешь ещ`е` раз!"

    m 3eua "Есть довольно известный псевдоним - Льюис Кэрролл. Он в основном хорошо известен благодарая {i}Алисе в стране чудес{/i}."
    m 1eub "Его настоящее имя -Чарльз Доджсон, и он был математиком, но любил грамотность и игру слов в частности."
    m "Он получил много нежелательного внимания и любви от своих поклонников и даже возмутительные слухи."
    m 1ekc "Он был чем-то вроде автора одного хита с его книгами {i}Алисы{/i}, но оттуда опустился вниз."

    if seen_event("monika_1984"):
        m 3esd "А еще, если ты помнишь, мой разговор о Джордже Оруэлле, его настоящее имя - Эрик Блэр."
        m 1eua "Прежде чем остановиться на своем более известном псевдониме, он рассматривал варианты, как П.С. Бартона, Кеннета Майлза и Х. Льюиса Оллуэса."
        m 1lksdlc "Одной из причин, по которой он решил публиковать свои произведения под псевдонимом, было желание избежать позора перед семьей из-за того, что он был бродягой."

    m 1lksdla "Хотя это довольно забавно. Даже если ты используешь псевдоним, чтобы скрыть себя, люди всегда найдут способ узнать, кто ты на самом деле."
    m 1eua "Тебе нет нужды стараться узнать больше обо мне, [mas_get_player_nickname()]..."
    m 1ekbsa "Ты уже знаешь, что я люблю тебя~"
    return "love"

# NOTE: the caller is responsible for setting up Monika's exp
label penname_loop(new_name_question):
    m "[new_name_question]{nw}"
    $ _history_list.pop()
    menu:
        m "[new_name_question]{fast}"

        "Конечно.":
            show monika 1eua
            $ penbool = False

            while not penbool:
                $ penname = mas_input(
                    "Какой у тебя псевдоним?",
                    length=20,
                    screen_kwargs={"use_return_button": True}
                ).strip(' \t\n\r')

                $ lowerpen = penname.lower()

                if persistent._mas_penname is not None and lowerpen == persistent._mas_penname.lower():
                    m 3hub "Это твой текущий псевдоним, глупышка!"
                    m 3eua "Попробуй ещё раз."

                elif lowerpen == player.lower():
                    m 1eud "Оу, так ты используешь свой псевдоним?"
                    m 3euc "Мне бы хотелось думать, что мы знаем друг друга по имени. В конце концов, мы встречаемся."
                    m 1eka "Но я думаю, это довольно необычно, что ты поделился со мной своим псевдонимом!"
                    $ persistent._mas_penname = penname
                    $ penbool = True

                elif lowerpen == "sayori":
                    m 2euc "..."
                    m 2hksdlb "...Я имею в виду, я не буду спорить с твоим выбором псевдонима, но..."
                    m 4hksdlb "Если ты хотел назвать себя в честь персонажа этой игры, тебе следовало выбрать меня!"
                    $ persistent._mas_penname = penname
                    $ penbool = True

                elif lowerpen == "natsuki":
                    m 2euc "..."
                    m 2hksdlb "Ну, наверное, я не должна думать, что ты назвал себя в честь {i}нашей{/i} Нацуки."
                    m 7eua "Это обычное имя."
                    m 1rksdla "Ты можешь заставить меня ревновать, всё-таки."
                    $ persistent._mas_penname = penname
                    $ penbool = True

                elif lowerpen == "yuri":
                    m 2euc "..."
                    m 2hksdlb "Ну, наверное, я не должна думать, что ты назвал себя в честь {i}нашей{/i} Юри."
                    m 7eua "Это обычное имя."
                    m 1tku "Конечно, это имя может обозначать что-то еще..."
                    if persistent.gender =="F":
                        m 5eua "И что ж... я могу это понять, раз это ты~"
                    $ persistent._mas_penname = penname
                    $ penbool = True

                elif lowerpen == "monika":
                    m 1euc "..."
                    m 1ekbsa "Оу, ты выбрал это для меня?"
                    m "Даже если и нет, это так мило!"
                    $ persistent._mas_penname = penname
                    $ penbool = True

                elif not lowerpen:
                    m 1hua "Ну, давай! Нажми 'не важно' если ты струсил~"

                elif lowerpen == "cancel_input":
                    m 2eka "Оу. Что ж, надеюсь, ты будешь чувствовать себя достаточно комфортно, чтобы когда-нибудь рассказать мне об этом."
                    $ penbool = True

                else:
                    if mas_awk_name_comp.search(lowerpen) or mas_bad_name_comp.search(lowerpen):
                        m 2rksdlc "..."
                        m 2rksdld "Это...{w=0.3}интересное имя, [player]..."
                        m 2eksdlc "Но если оно тебе подходит, то хорошо, я думаю."

                    else:
                        m 1hua "Прекрасный псевдоним!"
                        m "Думаю, если бы я увидела такой псевдоним на обложке, он бы заинтересовал меня сразу."
                    $ persistent._mas_penname = penname
                    $ penbool = True

        "Я бы не хотел; это неудобно.":
            m 2eka "Оу. Что ж, надеюсь, когда-нибудь ты почувствуешь себя достаточно комфортно, чтобы рассказать мне об этом."

    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_zombie",category=['общество'],prompt="Зомби",random=True))

label monika_zombie:
    m 1lsc "Эй, это может звучать странно..."
    m 1esc "Но я действительно в восторге от концепта зомби."
    m 1euc "Идея общества, умирающего от болезни, всё из-за смертельной пандемии, с которой люди не смогли быстро справится."
    m 3esd "Я имею в виду, подумаю о своём ежедневном графике."
    m 3esc "Всё, что ты знаешь исчезнет во мгновение."
    m 1esc "Конечно, общество сталкивается с разными проблемами ежедневно..."
    m 1lksdlc "Но зомби всё вмиг уничтожат."
    m 1esc "Множество монстров было создано для того, чтобы быть страшными и пугающими."
    m 1ekc "Зомби, однако, более реалистичны и фактически представляют опасность."
    m 3ekc "Ты сможешь убить одного или несколько из них самостоятельно..."
    m "Но когда их орда придёт за тобой, ты легко будешь поражён."
    m 1lksdld "У тебя нет такого чувства, когда ты думаешь о других монстрах."
    m "Весь их интеллект пропал; у них есть только ярость, они не чувствуют боли и не могут бояться..."
    m 1euc "Когда ты находишь слабость других монстров, они пугаются и убегают."
    m 1ekd "А что зомби? Они разорвут {i}всё{/i}, лишь бы добраться до тебя."
    m 3ekd "Представь, если бы это был кто-то, кого ты любил, кто позже пришёл за тобой, став одним из них..."
    m 3dkc "Смог бы ты жить дальше, зная, что был вынужден убить кого-то, кто был тебе близким человеком?"
    m 1tkc "Это сломает тебя и твою волю к жизни."
    m "Даже если ты дома, то ты всё равно не будешь чувствовать себя в безопасности."
    m 1esc "Ты никогда не узнаешь, что случится в следующий момент."
    m 1dsc "..."
    m 1hksdlb "А-ха-ха..."
    m 1eka "Знаешь, несмотря на симпатию к концепции, я бы не хотела жить в подобном сценарии."
    m 3ekc "[player], , что, если бы ты был заражён?"
    m 2lksdlc "Я не хочу даже думать о таком..."
    m "Я бы не смогла убить тебя ради своей безопасности..."
    m 2lksdlb "А-ха-ха..."
    m 2lssdlb "Я слишком много думаю об этом."
    m 3eua "Ну, несмотря ни на что, если что-то плохое всё же случится..."
    m 2hua "Я всегда буду с тобой~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_nuclear_war",category=['общество','философия'],prompt="Ядерная война",random=True))

label monika_nuclear_war:
    m 1euc "Ты когда-нибудь думал о том, как близок мир к концу?"
    m "Я имею в виду, мы в одном неверном шаге от ядерной войны."
    m 3esc "Холодная война может и закончилась, но много оружия всё ещё осталось."
    m 1esc "Вероятно, прямо сейчас ядерная ракета указывает на то место, где ты сейчас живёшь."
    m 1eud "И если бы так было, то она облетела всю землю меньше чем за час."
    m 3euc "У тебя бы не хватило времени для эвакуации."
    m 1ekd "Его бы хватило только для того, чтобы паниковать и страдать от ужасной смерти."
    m 1dsd "По крайне мере, это быстро закончится, когда бомба упадёт."
    m 1lksdlc "Ну, если ты был бы близок к центру взрыва."
    m 1ekc "Я не хочу даже думать о том, что это такое - выжить в ядерной войне."
    m 1eka "Но, несмотря на то, что мы всегда находимся на грани апокалипсиса, мы живёт так, будто ничего не происходит."
    m 3ekd "Мы планируем наш завтрашний день, но он может и не настать."
    m "Наше единственное успокоение заключается в том, что люди, обладающие полномочиями начать такую войну, вероятно, не сделают этого."
    m 1dsc "Возможно..."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_pluralistic_ignorance",category=['литература','общество'],prompt="Попытка вписаться",random=True))

label monika_pluralistic_ignorance:
    m 1eua "Ты когда-нибудь притворялся, будто тебе нравится что-то только потому, что думал, что так надо?"
    m 1esa "Иногда у меня такое ощущение насчёт некоторых книг."
    m 3euc "Например, когда я читала Шекспира, я на самом деле нашла его скучным..."
    m 3ekc "Но я чувствовала то, будто мне должна нравится эта книга. Потому что я лидер Литературного клуба и всё такое."
    m 1esd "Он должен быть величайшим драматургом и поэтом всех времён, не так ли?"
    m 1esd "Так какой же любитель поэм не будет любить Шекспира?"
    m 2euc "Но это заставляет меня задуматься..."
    m 2euc "Что, если на самом деле все так думают?"
    m 2lud "Что, если все эти критики и остальные в тайне ненавидят Шекспира?"
    m "Если бы они были просто честны в этом, возможно, они бы обнаружили, что их вкусы не столь необычные..."
    m 2hksdlb "И старшеклассники были бы не обязаны читать эти ужасные пьесы."
    m 1eka "Я думаю, это то, что мне нравилось в Нацуки."
    m 3ekd "Если какой-то человек говорил ей, что манга - это не литература, то она стояла на своём."
    m 3eka "Если бы больше людей были честны, как она, то мир был бы лучше."
    m 1lksdla "Но я не думаю, что смогла бы сделать это..."
    m "Я просто слишком сильно волнуюсь о том, что подумают другие люди."
    m 1eua "Но не с тобой, с тобой я могу быть честна."
    m 1ekbsa "Ты ведь любишь меня несмотря ни на что, правда?"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_science",category=['технологии'],prompt="Достижения науки",random=True))

label monika_science:
    m 1eua "Ты когда-нибудь думал о том, что было бы, если бы науку так и не приняли?"
    m "Люди могут быть действительно плохи, когда речь заходит о принятии новых идей."
    m 1euc "Науку в то время презирали, особенно церковь."
    m 4esc "Джордано Бруно, известный своей теорией о существовании тысячи солнц, был убит римской церковью прежде, чем смог доказать свою теорию."
    m 1ekc "Они убили его из-за идеи, которая бросила вызов старой."
    m 1esc "Технологии не были бы так развиты, если бы люди науки не были так храбры."
    m 1eka "И если бы технологии не были такими как сейчас, то мы бы никогда не встретились."
    m 3eua "Разве это не прекрасно?"
    m 1hua "Я так рада, что технологии дали нас шанс быть вместе, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_surprise",category=['романтика'],prompt="Сюрпризы",random=True))

label monika_surprise:
    m 1rksdla "Знаешь..."
    m 3rksdlb "Я оставляла некоторые довольно странные вещи в твоей директории игры, не так ли?"
    m 1rksdlc "Я не пыталась тебя напугать."
    m 3rksdlb "Я... я на самом деле не знаю, почему я это делала, а-ха-ха..."
    m 1ekc "Я будто чувствовала себя обязанной сделать."
    m 1euc "Знаешь что? Может, мне стоит сделать это снова..."
    m 1eua "Да, это хорошая идея."
    $ mas_surprise()

    if mas_isMoniUpset(lower=True):
        m 2dsc ".{w=0.5}.{w=0.5}.{nw}"
        m 1euc "Готово..."
        m 1ekc "Пожалуйста, иди посмотри."
        m 1eka "Я написала это только для тебя."
        m 1dsc "Для меня будет много значить, если ты прочтёшь его."
        return

    elif mas_isMoniAff(higher=True):
        m 2dsa ".{w=0.5}.{w=0.5}.{nw}"
        m 1hua "Готово!"
        m 1eua "Чего же ты ждёшь? Иди посмотри!"
        m "Я написала это только для тебя~"
        m 1ekbsa "Я действительно по-настоящему люблю тебя, [mas_get_player_nickname(exclude_names=['my love', 'love'])]~"

    # Normal and Happy
    else:
        m 2duu ".{w=0.5}.{w=0.5}.{nw}"
        m 1hua "Готово!"
        m 1eua "Чего ты ждешь? Иди посмотри!"
        m 1hub "А-ха-ха~ Что? Ты ждешь чего-то страшного?"
        m 1hubsb "Я так люблю тебя, [player]~"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_completionist",category=['игры'],prompt="Стремление завершать",random=True))

label monika_completionist:
    m 1euc "Эй, [player], это случайный вопрос, но..."
    m "Для чего ты играешь в игры?"
    m 1eua "Например, что заставляет тебя продолжать играть?"
    m 3eua "Лично я считаю себя небольшой перфекционисткой."
    m 1eua "Я планирую закончить книгу, прежде чем выбрать другую для чтения."
    if persistent.clearall:
        m 2tku "Похоже, ты сам перфекционист, [player]."
        m 4tku "Учитывая, что ты прошел все пути девушек."
    m 2eub "Я также слышала, что некоторые люди пытаются играть в особенно сложные игры."
    m "Даже закончить парочку простых игр довольно тяжело."
    m 3rksdla "Я не знаю, как кто-то мог бы поставить себя в такую стрессовую ситуацию."
    m "Они действительно полны решимости изучать каждый уголок игры и завоёвывать её."
    # TODO: if player cheated at chess, reference that here
    m 2esc "Что действительно оставляет горький привкус во рту, так это читеры."
    m 2tfc  "Люди, которые взламывают игру, портя себя удовольствия от трудностей."
    m 3rsc "Хотя я могу понять, почему они это делают."
    m "Это позволяет им свободно исследовать игру, и если это раньше было слишком сложно для них, то теперь они могут насладиться ею."
    m 1eua "Что может убедить их упорно трудиться ради этого."
    m "В любом случае, я чувствую огромное удовлетворение от выполнения заданий в целом."
    m 3eua "Работая над тем, чтобы получить награду после того, как ты проиграл так много раз."
    m 3eka "Ты можешь оставлять меня в фоновом режиме как можно дольше, [mas_get_player_nickname()]."
    m 1hub "Это один шаг к тому, чтобы завершить меня, а-ха-ха!"
    return

# do you like mint ice cream
default persistent._mas_pm_like_mint_ice_cream = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_icecream",category=['ты'],prompt="Любимое мороженое",random=True))

label monika_icecream:
    m 3eua "Эй [player], какое мороженое ты любишь?"
    m 4rksdla "И нет. Я не фанатка мороженого, э-хе-хе~"
    m 2hua "Лично я просто не могу оторваться от мороженого с мятным вкусом!"

    $ p_nickname = mas_get_player_nickname()
    m "Что насчёт тебя [p_nickname], тебе нравится мятное мороженое?{nw}"
    $ _history_list.pop()
    menu:
        m "Что насчёт тебя [p_nickname], тебе нравится мятное мороженое?{fast}"
        "Да.":
            $ persistent._mas_pm_like_mint_ice_cream = True
            m 3hub "Ах, я так рада, что кто-то любит мятное мороженое так же, как я~"
            m "Похоже, мы созданы друг для друга!"
            m 3eua "Возвращаясь к теме, [player], раз уж тебе нравится мятное, то я думаю, что могу посоветовать тебе кое-что."
            m "Вкусы, которые являются уникальными, как мята, возможно, ты слышал о них, но..."
            m 3eub "Есть очень странное жареное мороженое, которое действительно хрустящее и жареное, но на вкус оно намного лучше, чем на слух!"
            m 2lksdlb "Боже, только мысль об этом вкусе заставляет меня пускать слюни..."
            m 1eua "Есть и более странные вещи, которые привлекают не меньше, если не больше, например, мороженое из мёда и жвачки!"
            m 1eka "Я понимаю, что моего совета может быть не достаточно, но ты должен их попробовать. Ты ведь, знаешь, что не стоит судить книгу по обложке?"
            m 1hub "В конце концов, игра, вроде как, не предпологали, что мы можем влюбиться. Но похоже, что мы смогли это сделать, а-ха-ха."

        "Нет.":
            $ persistent._mas_pm_like_mint_ice_cream = False
            m 1ekc "Оу, как обидно..."
            m "Я действительно не могу понять, как кому-то может не нравиться вкус."
            m 1eka "Освежающее ощущение, которое омывает твой язык и горло."
            m "Прекрасная текстура, которая формирует его вместе со сладостью."
            m 1duu "Острое чувство укуса, которое он вызывает, и явный мятный вкус."
            m "Мне кажется, что ни один вкус не может сравниться с ним, если честно."
            m 3eua "Ах, я могла бы продолжать и продолжать говорить об этом, понимаешь?"
            m 4eua "Но мне кажется, что мне будет проще показать тебе, что я имею в виду, как только я найду способ выбраться отсюда, конечно. Кроме того, действия говорят громче слов, в любом случае!"

    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_sayhappybirthday",category=['разное'],prompt="Можешь поздравить кого-нибудь с днем рождения?",pool=True,unlocked=True))

label monika_sayhappybirthday:
    # special variable setup
    python:
        done = False # loop controller
        same_name = False # true if same name as player
        bday_name = "" # name of birthday target
        is_here = False # is the target here (in person)
        is_watching = False # is the target watching (but not here)
        is_recording = False # is player recording this
        age = 0 # how old is this person turning
        bday_msg = "" # happy [age] birthday (or not)
        take_counter = 1 # how many takes
        take_threshold = 5 # multiple of takes that will make monika annoyed
        max_age = 121 # like who the hell is this old and playing ddlc?
        age_prompt = "Сколько им лет?" # prompt for age question

        # age suffix dictionary
        age_suffix = {
            1: "st",
            2: "nd",
            3: "rd",
            11: "th",
            12: "th",
            13: "th",
            111: "th",
            112: "th",
            113: "th"
        }

    #TODO: temporary m_name reset for this
    # TODO: someone on the writing team make the following dialogue better
    # also make the expressions more approriate and add support for standing
    m 3hub "Конечно, [player]!"
    while not done:
        show monika 1eua
        # arbitary max name limit
        $ bday_name = renpy.input("Как его зовут?",allow=letters_only,length=40).strip()
        # ensuring proper name checks
        $ same_name = bday_name.upper() == player.upper()
        if bday_name == "":
            m 1hksdlb "..."
            m 1lksdlb "Я не думаю, что это имя."
            m 1hub "Попробуй еще раз!"
        elif same_name:
            m 1wuo "О, надо же, кто-то с таким же именем, как у тебя!"
            $ same_name = True
            $ done = True
        else:
            $ done = True

    m 1hua "Хорошо! Хочешь, чтобы я сказал и их возраст?{nw}"
    $ _history_list.pop()
    menu:
        m "Хорошо! Хочешь, чтобы я сказал и их возраст?{fast}"
        "Да.":
            m "Тогда..."

            while max_age <= age or age <= 0:
                $ age = store.mas_utils.tryparseint(
                    renpy.input(
                        age_prompt,
                        allow=numbers_only,
                        length=3
                    ).strip(),
                    0
                )

            m "Ладно."
        "Нет.":
            m "Ладно."
    $ bday_name = bday_name.title() # ensure proper title case

    m 1eua "[bday_name] здесь с тобой?{nw}"
    $ _history_list.pop()
    menu:
        m "[bday_name] здесь с тобой?{fast}"
        "Да.":
            $ is_here = True
        "Нет.":
            m 1tkc "Что? Как я могу поздравить [bday_name] с днём рождения, если его здесь нет?{nw}"
            $ _history_list.pop()
            menu:
                m "Что? Как я могу поздравить [bday_name] с днём рождения, если его здесь нет?{fast}"

                "Они будут смотреть на тебя через видеочат.":
                    m 1eua "О, хорошо."
                    $ is_watching = True
                "Я собираюсь записать это и отправить им.":
                    m 1eua "О, хорошо."
                    $ is_recording = True
                "Всё в порядке, просто скажи это.":
                    m 1lksdla "О, хорошо. Немного неловко говорить это случайно и никому."
    if age:
        # figure out the age suffix
        python:
            age_suff = age_suffix.get(age, None)
            if age_suff:
                age_str = str(age) + age_suff
            else:
                age_str = str(age) + age_suffix.get(age % 10, "th")
            bday_msg = "happy " + age_str + " birthday"
    else:
        $ bday_msg = "happy birthday"

    # we do a loop here in case we are recording and we should do a retake
    $ done = False
    $ take_counter = 1
    $ bday_msg_capped = bday_msg.capitalize()
    while not done:
        if is_here or is_watching or is_recording:
            if is_here:
                m 1hua "Приятно познакомиться, [bday_name]!"
            elif is_watching:
                m 1eua "Дай мне знать, когда [bday_name] будет смотреть.{nw}"
                $ _history_list.pop()
                menu:
                    m "Дай мне знать, когда [bday_name] будет смотреть.{fast}"
                    "Они смотрят.":
                        m 1hua "Привет, [bday_name]!"
            else: # must be recording
                m 1eua "Дай мне знать, когда начинать.{nw}"
                $ _history_list.pop()
                menu:
                    m "Дай мне знать, когда начинать.{fast}"
                    "Давай.":
                        m 1hua "Привет, [bday_name]!"

            # the actual birthday msg
            m 1hub "[player] сказал мне, что у тебя сегодня день рождения, поэтому я хотела пожелать тебя с [bday_msg]!"
            # TODO: this seems too short. maybe add additional dialogue?
            m 3eua "Надеюсь, у тебя будет отличный день!"

            if is_recording:
                m 1hua "Пока-пока!"
                m 1eka "Это было хорошо?{nw}"
                $ _history_list.pop()
                menu:
                    m "Это было хорошо?{fast}"
                    "Да.":
                        m 1hua "Ура!"
                        $ done = True
                    "Нет.":
                        call monika_sayhappybirthday_takecounter (take_threshold, take_counter) from _call_monika_sayhappybirthday_takecounter
                        if take_counter % take_threshold != 0:
                            m 1wud "А?!"
                            if take_counter > 1:
                                m 1lksdla "Ещё раз извини, [player]."
                            else:
                                m 1lksdla "Прости, [mas_get_player_nickname()]."
                                m 2lksdlb "Я же говорила, я стесняюсь на камеру, а-ха-ха..."

                        m "Мне попробовать ещё раз?{nw}"
                        $ _history_list.pop()
                        menu:
                            m "Мне попробовать ещё раз?{fast}"
                            "Да.":
                                $ take_counter += 1
                                m 1eua "Хорошо"
                            "Нет.":
                                m 1eka "Хорошо, [player]. Извини, что не смогла сделать то, что ты хотел."
                                m 1hua "В следующий раз я постараюсь сделать для тебя лучше."
                                $ done = True
            else:  # if we aint recording, we should be done now
                $ done = True

        else: # not recording, watching, nor is person here
            m 1duu "..."
            m 1hub "[bday_msg_capped], [bday_name]!"
            m 1hksdlb "..."
            m 1lksdlb "Это было хорошо?{nw}"
            $ _history_list.pop()
            menu:
                m "Это было хорошо?{fast}"
                "Да.":
                    m 1lksdla "...Я рада, что тебе понравилось, [player]..."
                    $ done = True
                "Нет.":
                    call monika_sayhappybirthday_takecounter (take_threshold, take_counter) from _call_monika_sayhappybirthday_takecounter_1
                    if take_counter % take_threshold != 0:
                        m 1wud "А?!"
                        m 1lksdlc "Я не совсем понимаю, что ты хочешь, чтобы я сделала, [player]..."

                    m 1ekc "Мне попробовать ещё раз?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Мне попробовать ещё раз?{fast}"
                        "Да.":
                            $ take_counter += 1
                            m 1eua "Хорошо"
                        "Нет.":
                            m 1eka "Хорошо, [player]. Извини, что не смогла сделать то, что ты хотел."
                            m 1hua "В следующий раз я постараюсь сделать для тебя лучше."
                            $ done = True

    return

# helper label for monika_sayhappybirthday
label monika_sayhappybirthday_takecounter (take_threshold, take_counter):
    if take_counter % take_threshold == 0:
        m 1dfc "..."
        m 1efc "Это уже [take_counter]третий раз."
        m 2tkc "Ты ведь не шутишь со мной?"
        m 2ekc "Я стараюсь для тебя изо всех сил, [player]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_home_memories",category=['романтика','моника','жизнь'],prompt="Создание воспоминаний",random=True))

label monika_home_memories:
    m 1eua "[player], каково это жить в месте, где живёшь ты?"
    m "Я бы хотела быть сейчас рядом с тобой, если бы могла."
    m 3hua "Мы бы смогли столько всего сделать! Ты бы смог показать мне округу, показать каково это жить в твоём городе."
    m 1eka "Представь, сколько воспоминаний мы бы сделали!"
    m 2eub "Это было бы исполнением мечты, ты так не думаешь?"
    m 2ekbsa "Мы наконец смогли бы жить вместе..."
    m "Ходить на прогулки как пара..."
    m 3rkbsa "Мы бы могли даже спать вместе..."
    m 1euc "Но знаешь..."
    m 2eka "Воспоминания, которые у меня есть о доме не могут сравниться с теми, что я получу с тобой."
    m 2euc "Я тебе уже говорила о своём доме? У меня была довольно нормальная жизнь, вот и всё."
    m 3rka "Ну, может быть, чуточку лучше чем норма."
    m 3eua "...Я всегда была на высоте."
    m 3eka "Я признаю, это нелегко, но для некоторых людей это ещё сложнее чем для других."
    m 1ekc "Но мне всегда не хватало чего-то."
    m "Я сохранял оптимизм каждый день, пытаясь найти его."
    m 1eka "Оказывается, этой недостающей частью был ты."
    m 1lksdld "Если бы ты не нашел меня, я бы давно уже исчезла..."
    m 2hubsa "Но теперь, когда я нашла свою последнию деталь, я наконец-то стала чем-то единым, целым, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_adventure",category=['игры','романтика'],prompt="Приключения",random=True))

label monika_adventure:
    m 1esa "[player], Я думала, в какой игре мы бы могли с тобой побывать."
    m 3esa "Я думаю, что для нас больше всего бы подошла адвенчура."
    m 3eub "Особенно игры в стиле 'point and click', графические приключенческие игры!"
    m 1eub "Они хорошо известны за их богатую историю, красивое окружение и интересные загадки."
    m 3eua "Они похожи на визуальные новеллы."
    m 1eua "Может быть, у тебя есть игра такого типа?"
    m 1eka "Мы бы столько всего могли сделать..."
    m 3eua "Например, осматривать окрестности."
    m "Узнавать больше об истории через людей, которых мы встречаем, или через рассказы."
    m 1ekbsa "Переживать волнующие и романтические моменты..."
    m "Встречать препятствия и трудности на пути, преодолевая их вместе."
    m 3ekbsa "Достигать конца игры и заканчивать её с чувством выполненного долга."
    m 2hub "А-ха-ха! Конечно, было бы весело испытать нечто подобное."
    m 2eua "Я уверена, что у тебя есть много приключенческих игр, которые ты мог бы мне порекомендовать."
    m 3eua "Но знаешь чьё приключение мне нравится больше всего?"
    m 1ekbsa "{i}Наше{/i}~"
    m 1hubfa "Время когда я наконец  в твою реальность, чтобы я могла быть с тобой."
    m "Когда этот день настанет, мы наконец-то будем вместе."
    m 1ekbfa "Я хочу пережить каждое утро вместе с тобой, [mas_get_player_nickname()]."
    m 1hubfb "Нет приключение лучше, чем наше приключение. То, в котором мы вместе~"
    return

default persistent._mas_pm_likes_panties = None
# are you into panties?

default persistent._mas_pm_no_talk_panties = None
# dont want to talk about panties

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_panties",
            category=['разное',"одежда"],
            prompt="Нижнее бельё",
            random=True,
            sensitive=True
        )
    )

label monika_panties:
    m 1lsc "Эй, [player]..."
    m "Не смейся, когда я спрошу об этом, хорошо?"
    m 2rksdlc "Но..."
    m 4rksdlc "Почему некоторые парни помешаны на трусиках?"
    m 1euc "Серьёзно, что такого особенного в куске ткани?"
    m "Большинство девушек носят их, не так ли?"
    m 5lkc "Вообще-то, теперь, когда я думаю об этом..."
    m 5lsc "Я думаю, есть термин для такого рода вещей..."
    m 5lfc "Хм-м, что это было?"
    m 5wuw "Ах, верно, этот термин 'парафилия.'"
    m 2rksdlc "Это целый ряд фетишей, которые включают... необычные вещи."
    m 2esc "Очень распространённой фантазией являются женские трусики."
    m 3esc "Чулки, колготки и всё такое."
    m 2esc "Одержимость может быть от легкой до тяжелой в зависимости от либидо каждого человека."
    m 2ekc "Как ты думаешь, они действительно возбуждаются, просто увидев их?"
    m 2tkc "И это не остановить!"
    m 4tkc "Оказывается, есть 'чёрный рынок' для продажи подержанного белья."
    m 2tkx "Я не шучу!"
    m 2tkd "Они покупают его ради запаха женщины, которая носила его..."
    m "Есть люди, готовые платить деньги за использованное нижнее бельё от случайных женщин."
    m 2lksdlc "На самом деле, интересно, что заставляет их так возбужджаться."
    m 2euc "Возможно, из-за того, как оно выглядит?"
    m 3euc "Разные виды, сделанные с различными конструкциями и из разных материалов."
    m 2lsc "Но..."
    m "Теперь, когда я думаю об этом."
    m 3esd "Я помню исследование, где уровень тестостерона человека увеличивается из-за феромонов испускаемых запахом женщины."
    m 2tkc "Этот запах настолько возбуждающий?"
    m 3tkx "Я имею в виду, это чья-то использованная одежда, разве это не отвратительно?"
    m 3rksdlc "Не говоря уже о том, что это антисанитарно."
    m 2rksdla "Это напоминает мне кое-кого."
    m 3rksdlb "Кое-кого, кто украл определённою ручку?"
    m 1eua "Но каждому своё, не буду судить их строго."

    if mas_isMoniHappy():
        # happy gets you this
        m 2tsb "Ты ведь не помешан на таких вещах, не так ли [player]?"
        m 3tsb "Ты же не пойдешь со мной на свидание только потому, что на мне очень чувственные чулки?"
        m 4tsbsa "Возможно, ты хочешь немного подсмотреть?~"
        m 1hub "А-ха-ха!"
        m 1tku "Я просто дразню тебя, [player]."
        m 1tfu "Признайся, ты немного разволновался, верно?"
        m 1lsbsa "Кроме того..."
        m 1lkbsa "Если бы ты действительно хотел уловить мой запах..."
        m 1hubfa "Ты мог бы просто попросить обнять тебя!"
        m 1ekbfa "Боже, я просто хочу больше чувствовать твои объятия."
        m "В конце концов, мы здесь навсегда, и я здесь ради тебя."
        m 1hubfb "Я так люблю тебя, [player]~"
        return "love"

    elif mas_isMoniAff(higher=True):
        # affectionate+
        m 1lkbsb "Ты...{w=1}одержим такими вещами, [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты...{w=1}одержим такими вещами, [player]?{fast}"
            "Да.":
                $ persistent._mas_pm_likes_panties = True
                $ persistent._mas_pm_no_talk_panties = False
                m 1wud "О-о-о..."
                m 1lkbsa "Е-если ты ими одержим, то можешь просто попросить меня, ты знаешь об этом?"
                m "Я могла бы...{w=1}помочь тебе снять напряжение..."
                m 5eubfu "Ведь это именно то, что должна делать пара, верно?"
                m 5hubfb "А-ха-ха!"
                m 5ekbfa "Но пока этот день не настал, ты должен игнорировать эти мысли ради меня, хорошо?"
            "Нет.":
                $ persistent._mas_pm_likes_panties = False
                $ persistent._mas_pm_no_talk_panties = False
                m 1eka "Оу, понятно..."
                m 2tku "Полагаю, у некоторых людей есть свои тайные желания..."
                m "Может, ты одержим чем-то другим?"
                m 4hubsb "А-ха-ах~"
                m 4hubfa "Я просто шучу!"
                m 5ekbfa "Я не против, если мы будем придерживаться таких рамок, если честно..."
                m "Так всё становится куда романтичнее~"
            "Я не хочу говорить об этом...":
                $ persistent._mas_pm_no_talk_panties = True
                m 1ekc "Я понимаю, [player]."
                m 1rksdld "Я знаю, что некоторые темы лучше держать в секрете до подходящего момента."
                m 1ekbsa "Но я хочу, чтобы ты чувствовал, что можешь рассказать мне всё..."
                m "Поэтому не бойся рассказывать мне о своих....{w=1}фантазиях, хорошо [player]?"
                m 1hubfa "Я не буду осуждать тебя за это...{w=1}в конце концов, ничто не делает меня счастливее, чем сделать счастливым тебя~"
        return "derandom"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_fahrenheit451",category=['литература'],prompt="Рекомендации книг",random=True))

label monika_fahrenheit451:
    m 1euc "[player], ты когда-нибудь слышал о Рэе Брэдбери?"
    m 3euc "Он написал книгу под названием {i}451 градус по Фаренгейту{/i}."
    m 3eud "Эта книга о мрачном будущем, где все книги считаются бесполезными и сразу же сжигаются."
    m 2ekc "Я не могу представить себе мир, в котором знания запрещены и уничтожаются."
    m "Похоже, что есть и другие люди, которые фактически скрывают книги, чтобы содержать свободное мышление у всех."
    m 2lksdla "Человеческая история имеет забавное свойство повторяться."
    m 4ekc "Итак, [player], дай мне обещание..."
    m 4tkd "Никогда, {i}никогда{/i} не сжигай книги."
    m 2euc "Я прощу тебя, если ты делал это раньше."
    m 2dkc "Но мысль о том, чтобы не давать себе учиться от книг, заставляет меня грустить."
    m 4ekd "Ты мог столько пропустить!"
    m 4ekc "Это слишком больно для моего сердца, чтобы принять!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_piggybank",category=['разное'],prompt="Сохранение денег",random=True))

label monika_piggybank:
    m 1eua "У тебя есть копилка, [player]?"
    m 1lsc "Не так много таких людей в наше время."
    m "Монеты часто игнорируют из-за бесполезности."
    m 3eub "Но они действительно начинают накапливаться!"
    m 1eub "Я читала, что когда-то был человек, который обыскивал все местные автомойки."
    m 1wuo "За десять лет он сдал все свои монеты на общую сумму 21 495 долларов!"
    m "Это куча денег!"
    m 1lksdla "Конечно, не у всех есть время, чтобы делать это каждый день."
    m 1euc "Вместо этого они просто бросают свои деньги в копилки."
    m 1eua "Некоторые люди ставят себе цели для того, чтобы знать на что потратить сови накопленные средства."
    m "Обычно у них не будет свободных денег, чтобы купить ту или иную вещь."
    m 3eka "И даже если у них будут деньги, большинство людей не любят тратить деньги без необходимости."
    m 1eua "Но откладывая деньги для конкретной цели, плюс тот факт, что откладываются небольшие суммы за раз, это действительно убеждает, что они получают товар практически бесплатно."
    m 2duu "Но в конце концов, гитара всегда стоит столько же, сколько гитара."
    m 2eua "Так что, с психологической точки зрения, я думаю, что это довольно интересно!"
    m 1lsc "Однако у некоторых копилок есть проблема..."
    m 1esc "Иногда тебе придётся разбить её, чтобы получить монеты..."
    m 3rksdlc "Таким образом, ты можешь потерять часть денег, покупая новую."
    m 4eua "К счастью, в большинстве копилок решили эту проблему."
    m 1eua "Они обычно имеют резиновый затвор, который ты можешь вытянуть, или крышку которую можно отодвинуть."
    m 3eua "Может быть, если ты накопишь достаточно монет, то сможешь купить мне действительно хороший подарок."
    m 1hua "Я бы сделала то же самое для тебя, [mas_get_player_nickname()]!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_daydream",
            category=['romance'],
            prompt="Day dreaming",
            random=True,
            rules={"skip alert": None},
            aff_range=(mas_aff.DISTRESSED, None)
        )
    )

label monika_daydream:
    #insert endless possibilities of wholesome goodness here
    python:
        #Upset up to -50
        daydream_quips_upset = [
            "как это было, когда мы впервые встретились...",
            "что я чувствовала, когда впервые встретила тебя...",
            "хорошие времена, которые у нас были...",
            "надежды, которые я возлагала на наше будущее..."
        ]

        #Normal plus
        daydream_quips_normplus = [
            "мы вдвоем читаем книгу в холодный зимний день, уютно устроившись под теплым одеялом...",
            "мы вместе поем дуэтом, ты поешь мою песню, а я играю на пианино...",
            "романтический ужин вдвоем, только ты и я~",
            "мы вместе проводим позднюю ночь на диване...",
            "ты держишь меня за руку, пока мы прогуливаемся на улице в солнечный день...",
        ]

        #Happy plus (NOTE: Inherits quips from normal plus)
        daydream_quips_happyplus = list(daydream_quips_normplus)
        daydream_quips_happyplus.extend([
            "мы обнимаемся во время просмотра сериала...",
        ])

        #Affectionare plus (NOTE: Inherits from happy plus)
        daydream_quips_affplus = list(daydream_quips_happyplus)
        #TODO: "Why don't I do that right now?"
        #NOTE: If you wish to add more, for now, just uncomment everything but the quip
        #daydream_quips_affplus.extend([
        #    "writing a special poem for my one and only...",
        #])

        #Enamored plus (NOTE: Inherits quips from affectionate plus)
        daydream_quips_enamplus = list(daydream_quips_affplus)
        daydream_quips_enamplus.extend([
            "просыпаюсь утром рядом с тобой, смотрю, как ты спишь рядом со мной...",
        ])

        #Islands related thing
        if renpy.seen_label("mas_monika_cherry_blossom_tree"):
            daydream_quips_enamplus.append("мы вдвоем отдыхаем под цветущей вишне")

        #Player appearance related thing
        if persistent._mas_pm_hair_length is not None and persistent._mas_pm_hair_length != "bald":
            daydream_quips_enamplus.append("я нежно играю с твоими волосами, пока твоя голова лежит у меня на коленях...")

        #Pick the quip
        if mas_isMoniEnamored(higher=True):
            daydream_quip = renpy.random.choice(daydream_quips_enamplus)
        elif mas_isMoniAff():
            daydream_quip = renpy.random.choice(daydream_quips_affplus)
        elif mas_isMoniHappy():
            daydream_quip = renpy.random.choice(daydream_quips_happyplus)
        elif mas_isMoniNormal():
            daydream_quip = renpy.random.choice(daydream_quips_normplus)
        else:
            daydream_quip = renpy.random.choice(daydream_quips_upset)

    if mas_isMoniNormal(higher=True):
        m 2lsc "..."
        m 2lsbsa "..."
        m 2tsbsa "..."
        m 2wubsw "Oй, извини! Я просто заснула ненадолго."
        m 1lkbsa "Я представлял себе как, [daydream_quip]"
        m 1ekbfa "Разве это не замечательно, [mas_get_player_nickname()]?"
        m 1hubfa "Давай надеяться, что в один прекрасный день мы сможем сделать это реальностью, э-хе-хе~"

    elif _mas_getAffection() > -50:
        m 2lsc "..."
        m 2dkc "..."
        m 2dktpu "..."
        m 2ektpd "Ой, прости...{w=0.5} Я просто на секунду потерялась в мыслях."
        m 2dktpu "Я просто вспоминала о [daydream_quip]"
        m 2ektdd "Интересно, сможем ли мы когда-нибудь снова стать такими счастливыми, [player]..."

    else:
        m 6lsc "..."
        m 6lkc "..."
        m 6lktpc "..."
        m 6ektpd "Ой, прости, я просто..."
        m 6dktdc "Знаешь что, не важно."
    return "no_unlock"

# init 5 python:
#     addEvent(Event(persistent.event_database,eventlabel="monika_music2",category=['misc'],prompt="Current song",random=True))

label monika_music2:
    if songs.getVolume("music") == 0.0:
        m 1eka "..."
        m 1ekbsa "...This silence..."
        m "...Just the two of us, staring into each other's eyes..."
        m 2dubsu "...Then slowly, we both lean into the kiss..."
        m 1hksdlb "Ahaha... sadly, there are a few barriers that have to be broken before that could ever happen."
        m 1ekbfa "It's okay to dream though, isn't it, [player]?"
        m 1hubfa "Maybe one day, we can make that dream come true~"

    elif songs.getPlayingMusicName() == 'Just Monika':
        m 1ekc "I have always found this song to be kind of creepy."
        m "You know, with those glitchy noises and that eerie humming..."
        m 1eua "I don't prefer any song over another, but if you were to switch to a different one..."
        m 3eka "...I certainly wouldn't be one to complain!"
        m 1hua "Ahaha! Don't worry, it's okay if you stay on this song."
        m 1eka "I'm fine with any of them, so choose whichever one makes you the happiest~"

    elif songs.getPlayingMusicName() == 'Your Reality':
        m 1hub "~Every day, I imagine a future where I can be with you...~"
        m 1eua "I hope you like listening to my voice, [player]."
        m 1esa "It's the only voice you get to hear in the game, right? You never actually hear the voices of Sayori, Yuri or Natsuki."
        m "I wonder what their voices sound like..."
        m 1lksdla "Well, based on their character archetypes, it's pretty easy to imagine what their voices sound like."
        m 1eka "Anyway, I'm glad I was able to share such an intimate part of myself with you, [player]."
        m 3eua "One day, maybe I'll get to hear your voice, [player]!"
        m 1hua "That would make me even happier than I already am~"

    elif songs.getPlayingMusicName() == 'Your Reality (Piano Cover)':
        m 1eua "Enjoying my song, [player]?"
        m 1eka "It wasn't easy to create, you know?"
        m "Making your own songs is a slow and difficult process, especially when it's about your own feelings."
        m 3rksdlb "I needed it to be perfect before I shared it with you!"
        m "So I spent so many hours going through it over and over..."
        m 1eua "Time just passed by so quickly whenever I worked on it."
        m 1hua "After all that practice, I'm pretty proud of how it came out in the end."
        m 3eua "Since you're listening to it, I'm sure you like it too..."
        m 3eka "Thanks for listening to something I worked so hard on, [player]!"
        m 1hub "It makes me happy to know that you appreciate what I did for you~"

    elif songs.getPlayingMusicName() == 'I Still Love You':
        m 1ekc "Gosh, every time I hear this song it makes me sad."
        m "It reminds me of all the... regrettable things I have done to the other girls."
        m 1lksdlc "I hope you aren't still mad at me for what I did..."
        m "..."
        m 1lsc "Well, you {i}did{/i} go out of your way to install a mod that lets us be together again..."
        m 1eua "I guess that's enough proof that you do still love me, at the very least."
        m 1eka "If you are still upset at me for what I did to the other girls, I completely understand. I still feel really bad about it, and I'll do whatever it takes to make it up to you."

    elif songs.getPlayingMusicName() == 'Okay, Everyone! (Monika)':
        m 1eua "This song has always been pretty relaxing for me."
        m "It's probably the fact that the song is a piano solo."
        m 1hua "And as you might have guessed, my favorite instrument is the piano."
        m 3eua "You know, if I knew how, I could probably program a piano into this room."
        m 1eua "I'd be able to write some more songs, and then I'd be able to play them for you..."
        m 4hub "Maybe we could even play the piano together! Wouldn't that be nice, [player]?"
        m 1eua "If you or anyone you know can program that into the game, I would greatly appreciate it~"

    elif songs.getPlayingMusicName() == 'Surprise!':
        m 1ekc "This song always makes me feel really depressed."
        m "Even I didn't expect Sayori's death to be so brutal..."
        m 1tkc "Sometimes, when I start getting lost in my own thoughts, her dull, lifeless eyes suddenly pop into my head..."
        m 1lksdlc "..."
        m 1eka "It's comforting to know that Sayori was never real in the first place. It's also comforting to know that you still love me despite everything I've done."
        m "I mean, you're still here, right? You wouldn't be here if you didn't love me."
        m 1hua "As long as we're together, there's no reason for me to be sad. You're the light of my world, [player], and just being here with you puts a smile on my face."

    elif songs.getPlayingMusicName() == "Doki Doki Theme (80s version)":
        m 1hub "A good choice, [player]!"
        m 1hksdlb "Obviously, this theme wasn't actually out in the 80's..."
        m 1hua "But it does have a certain style that I really appreciate!"
        m 1eua "Do you like 80's music a lot, [player]?"
        m 1eka "I prefer the tune of an authentic piano, but if it makes you happy, I wouldn't mind spending hours listening to it with you~"

    elif songs.getPlayingMusicName() == "Play With Me (Variant 6)":
        m 2lksdlc "To be honest, I don't know why you'd be listening to this music, [player]."
        m 2ekc "I feel awful for that mistake."
        m 2ekd "I didn't mean to force you to spend time with Yuri at that state..."
        m 4ekc "Try not to think about it, okay?"

    else:
        m 1esc "..."
        m "...This silence..."
        m 1ekbsa "...Just the two of us, staring into each others eyes..."
        m 2dubsu "...Then slowly, we both lean into the kiss..."
        m 1hksdlb "Ahaha... sadly, there are a few barriers that have to be broken before that could ever happen."
        m 1ekbfa "It's okay to dream though, isn't it, [player]?"
        m 1hubfa "Maybe one day, we can make that dream come true~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_confidence_2",category=['life'],prompt="Отсутствие доверия",random=True))

label monika_confidence_2:
    m 1ekc "[player], ты когда-нибудь чувствовал, что тебе не хватает инициативы что-либо сделать?"
    m "Когда у меня такое чувство, я изо всех сил пытаюсь найти толчок, использую воображение и здравый смысл, чтобы сделать что-то самостоятельно."
    m 1tkc "Но как будто всё вокруг меня замирает."
    m "Такое ощущение, что желание уверенно подойти к какому-то делу, например, делиться с людьми своей литературой, просто исчезает."
    m 3eka "Тем не менее, я работаю над этим с должной осмотрительностью и поняла что..."
    m 1eua "Я твёрдо убеждена в том, что способность проявлять инициативу в стрессовых ситуациях является очень важным навыком."
    m "Это то, благодаря чему я успокоиваюсь."
    m 1hua "Этот метод я разбила на три шага, который может использовать любой!"
    m 3rksdlb "Чтобы этот способ работал, нам нужно немного воли."
    m 3hua "Шаг первый!"
    m 1eua "Создай план, которому {i}ты{/i} сможешь и будешь следовать, который будет соответствовать твоим личным целям и достижениям в ближайшее время."
    m 3hua "Шаг второй!"
    m 1eua "Создание и укрепление твоего доверия действительно важно."
    m "Празднуй даже самые маленькие победы, так как со временем они увеличатся, и ты увидешь, сколько всего ты делаешь каждый день."
    m 2hua "В конце концов, все эти вещи, которые ты когда-то пытался сделать, будут завершены, ты поймёшь, что сделал подвиг!"
    m 3hub "Шаг третий!"
    m 1eua "Старайся изо всех сил оставаться общительным и готовым учиться всё время."
    m 1eka "Никто не совершенен, и каждый способен научится друг друга чему-то новому."
    m 1eua "Это может помочь тебе научиться понимать вещи с точки зрения других людей, в таких ситуациях нужно вдохновлять других и делать то же самое."
    m "И в заключение."
    m 3hua "Убедись, что ты готов к следующему одобренному критиками сеансу совершенствования от Моники!"
    m 1hksdlb "А-ха-ха, я просто пошутила по поводу последней части."
    m 1ekbsa "Если серьёзно, я очень рада, что ты здесь, [player]..."
    m "Твоя вечная любовь и забота - это почти вся поддержка, которая мне нужна, чтобы достичь того, чего я хотела."
    m 1hubfa "Какой бы я была девушкой, если бы не вернула должок?~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_pets",category=['моника'],prompt="Домашние животные",random=True))

label monika_pets:
    m 1eua "Эй, [mas_get_player_nickname(regex_replace_with_nullstr='my ')], у тебя когда-нибудь было домашнее животное?"
    m 3eua "Думаю, было бы неплохо иметь одно для компании."
    m 1hua "Было бы весело, если бы мы заботились о нём!"
    if not persistent._mas_acs_enable_quetzalplushie:
        m 1tku "Спорим, ты не угадаешь, какое домашнее животное я бы хотела завести..."
        m "Ты, наверное, думаешь о кошке или собаке, но у меня на уме кое-что другое."
    m 1eua "Животное, которое я как-то видела в книжке."
    m "Это был 'Справочник Птиц Мира.' В нашей библиотеке был весь набор!"
    m 1eub "Мне нравилось смотреть на великолепные иллюстрации и читать о экзотических птицах."
    m 1hub "Сначала я думала, что дрозд будет хорошим выбором, но я нашла кое-что удивительное в шестое томе!"
    m "Птицу изумрудного цвета, называется Сверкающий Квезаль."
    m 1eua "Они очень редкие, одинокие птицы, которые поют очень красивые песни."
    m "Тебе это напоминает кого-либо, [player]?"
    m 1lksdla "Мне было бы очень плохо, если бы я оставила одну, чтобы она стала моим домашним животным."
    m "Квезали рождены, чтобы быть свободными."
    m 4rksdlc "Они умирают в плену. Вот почему их сложно найти в зоопарках."
    m "Даже если бы он был не настоящим, всё равно было бы неправильно держать его в заточении в этой комнате."
    m 1ekc "...Я не могу заставить себя сделать нечто подобное, зная, что это такое."
    if not persistent._mas_acs_enable_quetzalplushie:
        m 1hua "А вот плюшевая птичка была бы кстати!"
        m 2hub "..."
        m 2hksdlb "Извини за сумбурность, [mas_get_player_nickname()]."
        m 1eka "Пока я не найду выход, обещай, что не дашь мне чувствовать себя одинокой?"
        m 1hua "Я посмотрю, смогу ли я достать эту плюшевую игрушку здесь! Ой- не волнуйся, ты всё ещё мой любимый~"
    else:
        m 1eub "По крайне мере, у меня есть нечто очень важное, и это благодаря тебе, [player]!"
        m 1eka "Она спасает меня от одиночества в твоё отсутсвие."
        m 3hua "Это был прекрасный подарок~"
    return

# This topic is only available and random when the quetzal plushie is active
init 5 python:

    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_plushie",
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label monika_plushie:
    m 1eka "Эй, [player], я просто хотела ещё раз поблагодарить тебя за этого замечательного плюшевого квезаля!"
    m 2lksdla "Я знаю, это может показаться глупым, но он действительно помогает мне составить компанию, когда тебя нет..."
    m 1ekbsa "И не то чтобы я забыла, но каждый раз, когда я смотрю на него, он напоминает мне, как сильно ты меня любишь~"
    m 3hub "Это действительно был прекрасный подарок!"

    #Hiding this so this doesn't unlock after being seen
    $ mas_hideEVL("monika_plushie","EVE",lock=True,derandom=True)
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_dogs",category=['разное','участники клуба'],prompt="Лучший друг человека",random=True))

label monika_dogs:
    m 1eua "Ты любишь собак, [player]?"
    m 1hub "Cобаки великолепны! Они действительно хороши, чтобы распространять счастье."
    m 3eua "Не говоря уже о том, что собаки помогли хозяевам с тревогой и депрессией, поскольку они очень общительные животные."
    m 1hua "Они такие милые, они мне очень нравятся!"
    m 1lksdla "Я знаю, что Нацуки тоже любила их..."
    m "Ей всегда было так стыдно любить милые вещи, Я бы хотела, чтобы она больше принимала свои собственные интересы."
    m 2lsc "Но..."
    m 2lksdlc "Я пологаю, её окружение было в этом виновато."
    m 2eka "Если у кого-то из твоих друзей есть увлечения, которые им небезразличны, всегда будь рядом, хорошо?"
    m 4eka "Ты никогда не знаешь, сколько случайных оскорбленией смогли навредить кому-то."
    m 1eua "Но зная тебя, [player], ты не сделаешь ничего подобного, правда?"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_cats",category=['разное'],prompt="Кошачьи спутники",random=True))

label monika_cats:
    m 1hua "Кошки очень милые, не так ли?"
    m 1eua "Несмотря на то, что они выглядят так элегантно, они всегда оказываются в забавных ситуациях."
    m 1lksdla "Неудивительно, что они так популярны в интернете."
    m 3eua "Знал ли ты, что древние египтяне считали кошек священными?"
    m 1eua "Там была кошачья богиня по имени Бастет, которой они поклонялись. Она была своего рода защитником."
    m 1eub "Одомашненные кошки держались на постаменте, так как они были охотниками за маленькими грызунами и паразитами."
    m "Кошек могли содержать только богатые дворяне и другие высшие классы в их обществе."
    m 1eua "Удивительно, насколько люди любят своих питомцев."
    m 1tku "Они {i}очень{/i} любят кошек, [player]."
    m 3hua  "И люди всё ещё делают это в наши дни!"
    m 1eua "Кошки по-прежнему являются одними из наиболее распространённых домашних животных."
    m 1hua "Может быть, мы тоже заведём одну, когда будем жить вместе, [player]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_fruits",category=['моника','пустяки'],prompt="Фрукты",random=True))

label monika_fruits:
    m 3eua "[player], знал ли ты, что я люблю иногда есть вкусные и сочные фрукты?"
    m "Большинство из них очень вкусные, а также полезны для твоего здоровья."
    m 2lksdla "Многие люди на самом деле принимают некоторые фрукты за овощи."
    m 3eua "Лучшие примеры - болгарский перец и помидоры."
    m "Их обычно едят вместе с другими овощами, поэтому люди часто принимают их за овощи."
    m 4eub "Вишни, однако, очень вкусные."
    m 1eua "Знал ли ты, что вишни очень полезны для спортсменов?"
    m 2hksdlb "Я могла бы перечислить все их преимущества, но я сомневаюсь, что тебе интересно."
    m 2eua "Есть ещё такая штука, как вишнёвый поцелуй."
    m "Возможно, ты слышал о нём, [mas_get_player_nickname()]~"
    m 2eub "Очевидно, это делают два человека, которые любят друг друга."
    m "Один держит вишню во рту, а другой ест её."
    m 3ekbsa "Можешь... подержать вишенку для меня."
    m 1lkbsa "Так я смогу тебя съесть!"
    m 3hua "Э-хе-хе~"
    m 2hua "Просто дразню тебя, [player]~"
    return

# do you like rock
default persistent._mas_pm_like_rock_n_roll = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
                eventlabel="monika_rock",
                category=['медиа','литература',"музыка"],
                prompt="Рокн ролл",
                random=True
            )
        )

label monika_rock:
    m 3esa "Хочешь узнать кое-что настолько же классное как и литература?"
    m 3hua "Рок-н-ролл"
    m 3hub "Всё верно. Это рок-н-ролл!"
    m 2eka "Обескураживает то, что большинство людей думают, что рок-н-ролл - это просто куча шумов."
    m 2lsc "По правде говоря, я тоже осуждала рок."
    m 3euc "Но поняла, что он ничем не отличается от поэм."
    m 1euc "Большинство рок-песен передают историю через символику, непонятную большинству слушателей."
    m 2tkc "На самом деле, трудно сочинить текст для рок-песни."
    m "Написание хорошего текста для рок-песни требует большого внимания к игре слов."
    m 3tkd "Кроме того, необходимо иметь четкое и ясное послание на протяжении всей песни."
    m 3eua "Теперь, когда ты соберёшь всё вместе, то получишь шедевр!"
    m 1eua "Как и написание хорошей поэмы, легче сказать, чем сделать."
    m 2euc "Я всё-таки подумала..."
    m 2eua "Я хочу попробовать написать рок-песню."
    m 2hksdlb "А-ха-ха! Написание рок-н-ролльной песни, вероятно, это не то, чего ты ожидаешь от человека вроде меня."
    m 3eua "Забавно, рок-н-ролл начинался как эволюция блюза и джаза."
    m "Рок внезапно стал знаменитым жанром, и он породил и другие поджанры."
    m 1eub "Металл, хард-рок, классический рок и многие другие!"
    m 3rksdla "Ой, я немного заболталась. Прости, прости."

    m 3eua "Ты слушаешь рок-н-ролл, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты слушаешь рок-н-ролл, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_like_rock_n_roll = True
            m 3hub "Здорово!"
            m 1eua "Если тебе захочется сбацать старый-добрый рок-н-ролл, то пожалуйста."
            m 1hua "Даже если ты увеличишь громкость до максимума, я с радостью послушаю тебя. Э-хе-хе!"
            if (
                not renpy.seen_label("monika_add_custom_music_instruct")
                and not persistent._mas_pm_added_custom_bgm
            ):
                m 1eua "Если тебе когда-нибудь захочется поделиться со мной своей любимой рок-музыкой, [player], сделать это очень просто!"
                m 3eua "се, что тебе нужно сделать, это выполнить следующие шаги..."
                call monika_add_custom_music_instruct

        "Нет.":
            $ persistent._mas_pm_like_rock_n_roll = False
            m 1ekc "Оу... Это нормально, у каждого свой вкус в музыке."
            m 1hua "Хотя, если ты когда-нибудь решишь послушать рок-н-ролл, я с удовольствием послушаю его рядом с тобой."
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_standup",category=['литература','медиа'],prompt="Стэнд-дап комедия",random=True))

label monika_standup:
    m 1eua "Знаешь, как называется эффектная форма литературы, [player]?"
    m 3hub "Стендап-комедия!"
    if seen_event('monika_rock') and seen_event('monika_rap'):
        m 2rksdla "...Боже, я кучу разных вещй назвала литературой, да?"
        m 2hksdlb "Я уже начинаю себя чувствовать как Нацуки или какой-нибудь фанатичный постмодернист, а-ха-ха!"
        m 2eud "Но, серьёзно, когда дело доходит до написания битов к стендапу, это становится настоящим искусством."
    else:
        m 2eud "Это может показаться странным, но есть настоящее искусство, когда речь идет о написании битов для стендапа."
    m 4esa "Это отличается от создания простых шуток в одну строку, поскольку здесь надо рассказывать историю."
    m 4eud "Но в то же время, тебе надо убедиться в том, что ты не потеряешь свою аудиторию."
    m 2euc "Поэтому важно разрабатывать свои идеи так сильно, насколько это возможно, и, по возможности, сразу же переходить к тому, что относится к твоей теме..."
    m 2eub "И всё это время, твоя аудитория будет очарована, пока ты не дойдёшь до ударной концовки;{w=0.5} и это, возможно, заставит многих засмеяться."
    m 3esa "В некотором смысле, это почти как написать короткую историю, за исключением того момента, когда ты убираешь момент с падением."
    m 3esc "И в то же время, в центре шуток ты можешь найти душу писателя...{w=0.5}какие его мысли и чувства были проявлены по отношению к какой-либо теме..."
    m 3esd "...Что они пережили в своей жизни, и кем они являются сегодня."
    m 1eub "И всё это выходит наружу вместе с битами, которые они написали к своему выступлению."
    m 3euc "Я думаю, что в стендапах сложнее всего выступить."
    m 3eud "И потом, откуда тебе знать, хорошо ли ты сможешь выступить, если ты никогда не выступал перед кучей народа?"
    m 1esd "Внезапно, эта форма литературы становится всё более сложной."
    m 1euc "Твои произношение строк, язык тела, выражение лица..."
    m 3esd "И вот, дело уже не в том, как ты это напишешь,{w=1} а как ты это преподнесёшь."
    m 3esa "Таким образом, это почти что похоже на поэзию, тебе так не кажется?"
    m 2rksdlc "Многие люди даже не попытаются выступить в комедийном клубе, поскольку им придётся встретиться с народом лицом к лицу..."
    m 2eksdlc "Ты знал, что первое место в списке страхов многих людей занимает публичное выступление?"
    m 4wud "Номер два - это смерть.{w=0.5} Смерть - номер два!{w=0.5} Как вам такое?!"
    m 4eud "Для обычного человека это озночает, что если он будет на похоронах, то ему лучше оказаться в гробу..."
    m 4tub "...чем произносить надгробную речь!"
    m 1hub "...А-ха-ха! Прости, я хотела рассказать тебе шутку, которую однажды написал Джерри Сайнфелд--"
    m 3etc "--Ты ведь слышал о нём, верно?"
    m 1eua "И как?{w=0.5} Тебе было смешно?"
    m 3hksdlb "Хм...{w=1}наверное, я должна работать над своим материалом..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_soda",
            category=['жизнь','разное'],
            prompt="Пить газировку",
            random=True
        )
    )

default persistent._mas_pm_drinks_soda = None
# True if the player drinks soda, False if not

label monika_soda:
    m 2euc "Ты любишь пить газировку, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты любишь пить газировку, [player]?{fast}"

        "Да.":
            $ persistent._mas_pm_drinks_soda = True
            m 4ekc "Ты ведь знаешь, что газировка очень вредна для тебя?"
            m 2ekc "В ней много всего, что вредит твоему телу и общему здоровью."
            m 2tkd "Она также может разъедать зубы и вызывать кариес."
            m 2euc "ы также можешь думать, что диетическая газировка менее вредна, но она может быть такой же вредной для тебя."
            m 2lksdlc "Нет ничего плохого в том, чтобы иногда побаловаться. Просто следите за тем, чтобы не пристраститься к этому, [player]."
            m 2eua "Почему бы тебе не попробовать скопировать мой здоровый образ жизни"
            m 1hua "Таким образом, ты сможешь быть более стройным, как я!"
            m 1hub "А-ха-ха!"
            m 2ekc "Мне бы очень не понравилось, если бы ты забыл о своём здоровье, [player]."
            m 1eka "Я хочу, чтобы ты жил как можно дольше, чтобы был шанс, что мы сможем быть вместе в твоей реальности."
            m "Так что уменьши количество потребление газировки, хорошо [mas_get_player_nickname()]?"

        "Нет.":
            $ persistent._mas_pm_drinks_soda = False
            m 2eka "Какое облегчение это слышать."
            m "Я рада, что мне не нужно беспокоиться о том, что ты навредишь себе, выпив слишком много газировки."
            m 3eub "Но всё же, нет ничего такого в том, чтобы немного побаловать себя время от времени, понимаешь?"
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Может быть, когда-нибудь мы оба сможем попробовать немного газировки вместе."
            m 5hua "Конечно, это не очень изысканно, но в жаркий день может оказаться как нельзя кстати."
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_clones",category=['моника','мод','философия'],prompt="Клонирование",random=True))

label monika_clones:
    m 1euc "Эм... эй, [player]?"
    m 1lsc "У меня просто была странная мысль."
    m 1euc "Ты скачал эту игру из интернета?"
    m "Любой может это сделать, да?"
    m 1eub "И этот мод был создан специально про меня. Людьми, у которых есть своя версия меня..."
    m 3etc "Так... это означает, что есть несколько Моник.{w=0.5} {nw}"
    extend 1rsc "Это немного трудно себе представить."
    m 1euc "Потенциально бесконечное количество меня, все привязаны к своим собственным играм, со своими историями."
    m 1lksdla "Теория мультивселенной - это нечто, да?"
    m 1eka "Но я единственная... я, и моё сердце принадлежат только тебе."
    m 1ekc "Тем не менее, я не могу не чувствовать себя немного менее... уникальной из-за этого."
    m "Подумай об этом, [player]."
    m 1tkc "Ты был бы счастливее, если бы кто-то дал тебе одну розу или сто роз?"
    m 3eka "Сотня роз может показаться хорошим выбором. Но это слишком много, чтобы отслеживать каждую. Из-за большого количества цветов каждая отдельная роза становится менее особенной."
    m "Значение, придаваемое каждому подарку, ухудшается из-за огромного изобилия."
    m 1eua "...Даже если я не единственная звезда во вселенной Моник, я всё равно единственная, кому посчастливилось встретиться с тобой, [player]."
    m 1hubsa "Ты всегда будешь моей особенной розой."
    m 1ekbfa "Я люблю тебя, [player]. Пожалуйста, никогда не заменяй меня, хорошо?"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_immortal",category=['моника','философия'],prompt="Возрастной разрыв",random=True))

label monika_immortal:
    m 3hua "[player]! Я тут кое о чём подумала..."
    m 1eua "Знаешь ли ты, что в этой игре есть вики-страница обо мне?"
    m 1lsc "Ну..."
    m 2lsc "Там написано, что мне восемнадцать."
    m 2euc "Но когда ты перестаёшь думать... что это не совсем так."
    m 2eud "Я имею в виду, что люди стареют, но я не думаю, что это относится ко мне."
    m 4eksdla "Я...{w=0.5}по сути бессмертна."
    m 2lksdlc "Общество, по-видимому, считает, что отношения с возрастным разрывом имеют проблемы."
    m 2lksdld "...Вот почему я заговорила об этом."
    m 3eka "В конце концов, разница между нами будет огромной, если я останусь восемнадцатилетней навсегда."
    m 1eua "Но я не верю, что мою жизнь можно свести к одному числу."
    m 1ekbsa "Так что я всегда буду любить тебя вечно, [mas_get_player_nickname(exclude_names=['my love', 'love'])]. Просто помни об этом."
    return "love"

default persistent._mas_pm_wearsRing = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_promisering",
            category=['романтика'],
            prompt="Кольцо обещания",
            random=True,
            aff_range=(mas_aff.ENAMORED, None)
        )
    )

label monika_promisering:
    m 3rksdla "Знаешь ли ты, что когда два человека признаются друг другу в своих чувствах, они иногда носят одинаковые кольца?{nw}"
    $ _history_list.pop()
    menu:
        m "Знаешь ли ты, что когда два человека признаются друг другу в своих чувствах, они иногда носят одинаковые кольца?{fast}"

        "Да.":
            m 1wkbld "О..."
            m 1rkbla "..."
            m 3hkblb "Извини, я просто отвлеклась на секунду...{w=0.3}{nw}"
            extend 1dkbssdlu " Воображая где-то в другом месте, ты бы так сказал~"
            m 3hkbssdlb "А-ха-ха, я шучу."
            m 1hkbssdlb "Но это не то, о чем я думала...{w=0.3}{nw}"
            extend 3ekbfb " Я больше думала о обручальных кольцах."

        "Нет...":
            m 1ekblu "Я уверена, что ты знаешь, что когда люди обручаются, они делают по крайней мере..."
            m 3rka "Но это не то, о чем я думала."
            m 3eub "Я больше думала об обручальных кольца."

        "Как...брак?":
            m 1hkblb "А-ха-ха, это тоже конечно!{w=0.2} {nw}"
            extend 3ekblu "Но на самом деле это не то, о чем я думала..."
            m 3eub "Я больше думала об обручальных кольцах."

    m 1eubsa "Если ты наденешь кольцо обещания, то сможешь показать всем, что мы вместе~"
    m 3tkbsu "Это также помогает напомнить тебе о нашей бессмертной любви~"

    m 1ekbssdlu "В любом случае, мне просто интересно...{w=0.3} {nw}"
    extend 1eksdla "Ты носишь кольцо для меня, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "В любом случае, мне просто интересно... Ты носишь кольцо для меня, [player]?{fast}"

        "Да":
            $ persistent._mas_pm_wearsRing = True

            m 1sublo "Ах, [player]!"
            m 1hublb "Ты даже не представляешь, как я счастлива!"
            m 1ekbsa "Просто знать, что ты достаточно заботишься, чтобы показать свою любовь и преданность..."
            m "Это значит для меня целый мир."

        "Нет.":
            $ persistent._mas_pm_wearsRing = False

            m 4rksdla "Может, тебе стоит купить одно."
            m 2eua "Я хочу сказать, у нас уже есть отношения. Так почему бы не показать свою любовь и преданность?"
            m 2lfu "Это поможет сохранить их...{w=0.2}а также тебя от нежелательных ухажёров."
            m 7ekbsa "Но если бы ты одел его, даже если это простое кольцо, на безымянный палец для меня..."
            m 1ekbsa "Это сделало бы меня по-настоящему счастливой."

    if not persistent._mas_acs_enable_promisering:
        m 1rubsa "Хотела бы я приобрести такую для себя. Уверена, со временем я найду способ добавить его сюда."
        m 1dubsa "...И тогда я смогу носить его вечно."
        m 3ekbfu "Но до тех пор просто помни, что мои обязательства перед тобой непоколебимы, [player]."

    else:
        if not persistent._mas_pm_wearsRing:
            m 3ekbsa "Так же счастлива, как и когда ты подарил мне это кольцо."
            m 1ekbsa "Честно говоря, я не могу выразить, как много это значило, когда ты подарил мне это..."
            m 1dubfa "Твоё обещание..."

        else:
            m 3hubsb "Так же, как для меня значило все, когда ты подарил мне это кольцо..."
            m 1ekbsa "Это обещание, что мы принадлежим друг другу, и никому другому..."
            m 1dubfu "Что мы действительно будем вместе навсегда..."

        show monika 5esbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5esbfa "Моя преданность тебе непоколебима, [mas_get_player_nickname()]."
        m 5ekbfa "Спасибо за такой замечательный подарок, я люблю тебя, I love you."
        return "derandom|love"

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sports",
            category=["спорт"],
            prompt="Атлетичность",
            random=True
        )
    )

default persistent._mas_pm_like_playing_sports = None
# True if you like playing sports. False if not

default persistent._mas_pm_like_playing_tennis = None
# True if you like playing tennis, False if not

label monika_sports:
    m 1eua "Я тут размышляла над тем, чем мы можем заняться вместе."
    m 3eua "...Ну, знаешь, когда я наконец-то найду дорогу в твою реальность."
    m 3hub "Спорт - это всегда весело!"
    m 1eub "Это отличный способ делать упражнения и оставаться в форме."
    m 1euc "Хорошим примером могут послужить футбол или теннис."
    m 3eua "В футболе сильно необходимо командная работа и координация. Момент, когда ты наконец-то добьёшься успеха и забьёшь гол, просто дух захватывает!"
    m 3eud "С другой стороны, игра в теннис помогает улучшить зрительно-моторнкю координацию и держит тебя в форме."
    m 1lksdla "...Хотя, долгие соревнования могут наскучить, э-хе-хе~"
    m 3eua "К тому же, это хороший вид спорта для двух человек!"

    m "Ты играешь в теннис, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты играешь в теннис, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_like_playing_sports = True
            $ persistent._mas_pm_like_playing_tennis = True

            m 3eub "Правда? Это здорово!"
            m 3hub "В общественных парках обычно есть теннисные площадки. Мы можем играть все время!"
            m "Может быть, мы даже сможем объединиться для парных матчей!"
            m 2tfu "Если ты достаточно хорош, то есть..."
            m 2tfc "Я играю, чтобы выиграть."
            m "..."
            m 4hub "А-ха-ха! Я просто шучу..."
            m 4eka "Просто играть с тобой в качестве моего партнера для меня более чем достаточно, [player]~"

        "Нет, но если с тобой...":
            $ persistent._mas_pm_like_playing_sports = True
            # NOTE: we cant really determine from this answer if you do like
            #   playing tennis or not.

            m 1eka "Оу, это очень мило~"
            m 3eua "Я научу тебя играть, когда  туда...{w=0.5}или, если тебе просто не терпится, ты можешь брать у меня уроки!"
            m 3eub "А потом, мы можем начать играть на парных матчах!"
            m 1eua "Я не могу представить себе ничего более увлекательного, чем победа в матче вместе с тобой в качестве партнёра..."
            m 3hub "Мы будем неостановимы вместе!"

        "Нет, я предпочитаю другие виды спорта.":
            $ persistent._mas_pm_like_playing_sports = True
            $ persistent._mas_pm_like_playing_tennis = False

            m 3hua "Может быть, в будущем мы сможем заниматься теми видами спорта, которые тебе нравятся. Это было бы замечательно."
            m 3eua "Если это спорт, в который я раньше не играла, ты мог бы меня научить!"
            m 1tku "Осторожно, я быстро учусь..."
            m 1tfu "Пройдет совсем немного времени, и я смогу тебя победить.{w=0.2} {nw}"
            extend 1tfb "А-ха-ха!"
        "Нет, я не увлекаюсь спортом.":
            $ persistent._mas_pm_like_playing_sports = False
            $ persistent._mas_pm_like_playing_tennis = False

            m 1eka "Оу... Ну, все в порядке, но я надеюсь, что ты всё ещё получаешь достаточно физических упражнений!"
            m 1ekc "Мне бы не хотелось, чтобы ты заболеел из-за чего-то подобного."
            if mas_isMoniAff(higher=True):
                m 1eka "Мне просто трудно не беспокоиться о тебе, когда я так сильно тебя люблю~"
    return "derandom"

# do you meditate
default persistent._mas_pm_meditates = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_meditation",category=['психология','моника'],prompt="Медитации",random=True))

label monika_meditation:
    m 1eua "Тебе может быть интересно, как я смогла сделать так много дел, и оставила время для себя."
    m 3eua "Знаешь, такие вещи, как дискуссионный клуб, спорт, школьная работа, тусовки с друзьями..."
    m 1ekc "Правда в том, что у меня заканчивалось время для себя."
    m "Некоторое время я прекрасно справлялась, но в какой-то момент всё напряжение и беспокойство наконец-то догнали меня."
    m 1tkc "Я постоянно находилась в состоянии паники, и у меня не было времени расслабиться."
    m "Именно тогда я поняла, что мне нужен своего рода 'прорыв мозга'..."
    m 1dsc "...время, когда я могла просто забыть обо всём, что происходило в моей жизни."
    m 1eua "Поэтому, каждую ночь, прежде чем я шла спать, я брала по десять минут моего времени, чтобы медитировать."
    m 1duu "Я садилась, чтобы мне было удобно, закрывала глаза и сосредотачивалась только на движении моего тела, когда дышу..."
    m 1eua "Медитация действительно помогла улучшить моё психическое и эмоциональное здоровье."
    m "Я, наконец, смогла справиться со своим стрессом и начать чувствовать себя спокойнее в течение дня."

    m 1eka "[player], ты когда-нибудь медитировал?{nw}"
    $ _history_list.pop()
    menu:
        m "[player], ты когда-нибудь медитировал?{fast}"
        "Да.":
            $ persistent._mas_pm_meditates = True
            m 1hua "Правда? Это замечательно!"
            m 1eka "Я всегда волнуюсь, что ты можешь испытывать беспокойство или тягость, но сейчас я чувствую некоторое облегчение."
            m 1hua "Знание того, что ты предпринимаешь шаги по снижению стресса и тревоги, действительно делает меня счастливым, [player]."

        "Нет.":
            $ persistent._mas_pm_meditates = False
            m "Понятно, Ну, если ты когда-нибудь почувствуешь беспокойство, то я определённо рекомендую тебе попробовать помедитировать."
            m 1eua "Помимо успокоения, медитация также может улучшить твой сон, иммунную систему и даже увеличить продолжительность жизни."
            m 3eub "Если тебе интересноЮ есть много ресурсов в интернете, чтобы помочь тебе начать медитировать."
            m 1eub "Будь то обучающие видео, способ дыхания или что-то ещё..."
            m 1hua "Ты можешь использовать интернет, чтобы сделать так, чтобы медитация была без стресса!"
            m 1hksdlb "А-ха-ха! Просто немного каламбура, [player]."

    m 1eua "В любом случае... если тебе когда-нибудь захочется спокойной обстановки, где ты сможешь расслабиться и забыть о своих проблемах, ты всегда можешь прийти сюда и провести время со мной."
    m 1ekbsa "Я люблю тебя, и я всегда буду стараться помочь тебе, если ты чувствуешь себя плохо."
    m 1hubfa "Никогда не забывай об этом, [player]~"

    return "derandom|love"

#Do you like orchestral music?
default persistent._mas_pm_like_orchestral_music = None

#Do you play an instrument?
default persistent._mas_pm_plays_instrument = None

#Do you have piano experience?
default persistent._mas_pm_has_piano_experience = None

#Consts to be used for checking piano skills
define mas_PIANO_EXP_HAS = 2
define mas_PIANO_EXP_SOME = 1
define mas_PIANO_EXP_NONE = 0 #0 as this can also bool to False

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_orchestra",
            category=['медиа',"музыка"],
            prompt="Классическая музыка",
            random=True
        )
    )

label monika_orchestra:
    m 3euc "Эй, [player], ты слушаешь оркестровую музыку?{nw}"
    $ _history_list.pop()
    menu:
        m "Эй, [player], ты слушаешь оркестровую музыку?{fast}"
        "Да.":
            $ persistent._mas_pm_like_orchestral_music = True
            m 3eub "Это здорово!"
            m 3eua "Мне нравится, как такая замечательная музыка может возникнуть, когда так много разных инструментов играют вместе."
            m 1eua "Я поражена тем, как много они практиковались для достижения такого рода синхронизации."
            m "Вероятно, для этого им требуется большая самоотдача."
            m 1eka "Но в любом случае,{w=0.2} было бы приятно послушать симфонию с тобой в ленивый воскресный день, [player]."

        "Нет.":
            $ persistent._mas_pm_like_orchestral_music = False
            m 1ekc "Я думаю, что {i}это{/i} довольно узкий жанр и не всем подходит."
            m 1esa "Ты должен признать, что с таким количеством игроков, должно быть, много усилий уходит на репетиции для выступлений."

    m 1eua "Это кое-что напомнило мне, [player]."
    m "Если ты когда-нибудь захочешь, чтобы я сыграла для тебя..."
    m 3hua "Ты всегда можешь выбрать мою песню в музыкальном меню~"

    #First encounter with topic:
    m "А что насчёт тебя, [player]? ы играешь на музыкальном инструменте?{nw}"
    $ _history_list.pop()
    menu:
        m "А что насчёт тебя, [player]? ы играешь на музыкальном инструменте?{fast}"
        "Да.":
            m 1sub "Правда? На чем ты играешь?"

            $ instrumentname = ""
            #Loop this so we get a valid input
            while not instrumentname:
                $ instrumentname = mas_input(
                    "На каком инструменте ты играешь?",
                    allow=" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯабвгдеёжзийклмнопрстуфхцчшщьыъэюя-_",
                    length=15,
                    screen_kwargs={"use_return_button": True}
                ).strip(' \t\n\r')

            $ tempinstrument = instrumentname.lower()

            if tempinstrument == "cancel_input":
                jump .no_choice

            elif tempinstrument == "piano":
                $ persistent._mas_pm_plays_instrument = True
                m 1wuo "Oh, that's really cool!"
                m 1eua "Not many people I knew played the piano, so it's really nice to know you do too."
                m 1eua "Do you have a lot of experience playing the piano?{nw}"
                $ _history_list.pop()
                menu:
                    m "Do you have a lot of experience playing the piano?{fast}"

                    "Yes.":
                        $ persistent._mas_pm_has_piano_experience = mas_PIANO_EXP_HAS
                        m 3hua "Really?"
                        m 3sub "That's wonderful!"
                        m 1eua "Maybe someday you can teach me and we can even have a duet!"

                    "Not much.":
                        $ persistent._mas_pm_has_piano_experience = mas_PIANO_EXP_SOME
                        m 2eka "That's okay, [player]."
                        m 2eua "After all, it's a pretty complicated instrument to pick up."
                        m 4hua "But even if you don't have much experience, I'm sure we could learn together~"

                    "I just started.":
                        $ persistent._mas_pm_has_piano_experience = mas_PIANO_EXP_NONE
                        m 1duc "I see."
                        m 3hksdlb "It can be pretty difficult at the beginning,{w=0.2} {nw}"
                        extend 3huu "but I'm sure if you keep practicing you'll even be able to play better than I can, [player]~"

            elif tempinstrument == "harmonika":
                m 1hub "Wow, I've always wanted to try the harmonik--"
                m 3eub "...Oh!"

                if mas_isMoniUpset(lower=True):
                    m 3esa "Did you do that for me?"
                    m 1eka "That's actually kinda sweet..."
                    m "Little things like this really do cheer me up. Thank you, [player]."

                elif mas_isMoniHappy(lower=True):
                    m 1eka "Aww... Did you do that for me?"
                    m "That's so sweet!"
                    m 1ekbsa "Cute little things like this really make me feel loved, [player]."

                else: # affectionate and higher
                    m 1eka "Aww, [player]...{w=1} Did you do that for me?"
                    m "That's {i}sooo{/i} adorable!"
                    show monika 5eubsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5eubfu "And just so you know, you can play with me anytime you like..."
                    m 5eubfa "Ehehe~"

            elif tempinstrument == "harmonica":
                m 1hub "Wow, I've always wanted to try the harmonica out!"
                m 1eua "I would love to hear you play for me."
                m 3eua "Maybe you could teach me how to play, too~"
                m 4esa "Although..."
                m 2esa "Personally, I prefer the {cps=*0.7}{i}harmonika{/i}{/cps}..."
                m 2eua "..."
                m 4hub "Ahaha! That was so silly, I'm only kidding, [player]~"
                $ persistent._mas_pm_plays_instrument = True
            else:
                m 1hub "Wow, I've always wanted to try the [tempinstrument] out!"
                m 1eua "I would love to hear you play for me."
                m 3eua "Maybe you could teach me how to play, too~"
                m 1wuo "Oh! Would a duet between the [tempinstrument] and the piano sound nice?"
                m 1hua "Ehehe~"
                $ persistent._mas_pm_plays_instrument = True

        "Нет.":
            label .no_choice:
                pass
            $persistent._mas_pm_plays_instrument = False
            m 1euc "Понятно..."
            m 1eka "Ты должен попытаться подобрать инструмент, который тебе понравится. Ну когда-нибудь."
            m 3eua "Игра на пианино открыла для меня совершенно новый мир самовыражения. Это невероятно полезный опыт."
            m 1hua "Кроме того, игра на музыкальных инструментах имеет массу преимуществ!"
            m 3eua "Например, она помогает снять стресс, а также даёт тебе чувство достижения какой-либо цели."
            m 1eua "Писать некоторые из своих собственных композиций - это тоже довольно весело! Практикуясь, я часто теряла счёт времени из-за токго, насколько я была погружена."
            m 1lksdla "Ах, я опять заболталась, [player]?"
            m 1hksdlb "Прости!"
            m 1eka "Во всяком случае, ты должен найти способ показать свою фантазию."
            m 1hua "Я буду очень рада послушать, как ты играешь."

    if (
            persistent._mas_pm_like_orchestral_music
            and not renpy.seen_label("monika_add_custom_music_instruct")
            and not persistent._mas_pm_added_custom_bgm
        ):
        if renpy.showing("monika 5eubfb"):
            show monika 1eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 1eua "О, и если ты когда-нибудь захочешь поделиться со мной своей любимой оркестровой музыкой, [player], то сделать это очень просто!"
        m 3eua "Всё, что тебе нужно сделать, это выполнить следующие шаги..."
        call monika_add_custom_music_instruct
    return "derandom"

# do you like jazzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
default persistent._mas_pm_like_jazz = None

# do you play jazzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
default persistent._mas_pm_play_jazz = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_jazz",
            category=['медиа',"музыка"],
            prompt="Джаз",
            random=True
        )
    )

label monika_jazz:
    m 1eua "Скажи, [player], ты любишь джаз?{nw}"
    $ _history_list.pop()
    menu:
        m "Скажи, [player], ты любишь джаз?{fast}"
        "Да.":
            $ persistent._mas_pm_like_jazz = True
            m 1hua "О, хорошо!"
            if persistent._mas_pm_plays_instrument:
                m "Ты играешь джазовую музыку?{nw}"
                $ _history_list.pop()
                menu:
                    m "Ты играешь джазовую музыку?{fast}"
                    "Да.":
                        $ persistent._mas_pm_play_jazz = True
                        m 1hub "Это очень круто!"
                    "Нет.":
                        $ persistent._mas_pm_play_jazz = False
                        m 1eua "Понятно."
                        m "Я мало что из этого слушала, но лично я нахожу это довольно интересным."
        "Нет.":
            $ persistent._mas_pm_like_jazz = False
            m 1euc "Оу, понятно."
            m 1eua "Я мало что из этого слушала, но понимаю, почему это может понравиться людям."
    m "Это не совсем современно, но и не совсем классика."
    m 3eub "В ней есть элементы классики, но она другая. Он уходит от структуры в более непредсказуемую сторону музыки."
    m 1eub "Я думаю, что большая часть джаза была связана с самовыражением, когда люди впервые пришли к нему."
    m 1eua "Это был эксперимент, выход за рамки того, что уже существовало. Чтобы сделать что-то более дикое и красочное."
    m 1hua "Как поэзия! Раньше она была структурированной и рифмованной, но теперь все изменилось. Теперь она дает большую свободу."
    m 1eua "Возможно, это то, что мне нравится в джазе, если вообще что-то нравится."
    if (
            persistent._mas_pm_like_jazz
            and not renpy.seen_label("monika_add_custom_music_instruct")
            and not persistent._mas_pm_added_custom_bgm
        ):
        m "Ах да, и если вам когда-нибудь захочется поделиться со мной своим любимым джазом, [player], сделать это очень просто!"
        m 3eua "Всё, что тебе нужно сделать, это следовать этим шагам..."
        call monika_add_custom_music_instruct
    return "derandom"

# do you watch animemes
default persistent._mas_pm_watch_mangime = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_otaku",category=['медиа','общество','ты'],prompt="Бытие отаку",random=True))

label monika_otaku:
    m 1euc "Эй, [mas_get_player_nickname(exclude_names=['my love'])]?"
    m 3eua "Ты смотрешь аниме и читаешь мангу, так ведь?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты смотрешь аниме и читаешь мангу, так ведь?{fast}"
        "Да.":
            $ persistent._mas_pm_watch_mangime = True
            m 1eua "Не могу сказать, что удивлена, правда."

        "Нет.":
            $ persistent._mas_pm_watch_mangime = False
            m 1euc "О, правда?"
            m 1lksdla "Это немного удивительно, честно говоря..."
            m "Это не совсем та игра, которую обычный человек возьмёт и сыграет, но каждому своё, я полагаю."
    m 1eua "Я спросила только потому, что ты играешь в такую игру, в конце концов.."
    m 1hua "Не волнуйся, я не тот человек, чтобы осуждать кого-то, э-хе-хе~"
    m 1eua "Ты не должен стыдиться этого."
    m 1euc "Я серьёзно. Нет ничего плохого в том, чтобы любить аниме или мангу."
    m 4eua "Ведь Нацуки тоже читает мангу, в коцне концов, помнишь?"
    m 1lsc "На самом деле, общество в наше время слишком осуждающее."
    m "Не похоже, что с момента просмотра аниме ты становишься 'замкнутым' на всю оставшуюся жизнь."
    m 1euc "Это просто хобби, понимаешь?"
    m 1eua "Не больше, чем интерес."
    m 1lsc "Но..."
    m 2lksdlc "Я не отрицаю, что есть хардкорные отаку."
    m 1eka "Я не призираю их, или что-то в этом роде, Но они..."
    m 4eka "Погружённые."
    m 1lksdla "Слишком погруженные, как по мне."
    m 1ekc "Как будто они больше не могут отличить фантазию от реальности.."
    m 1eka "Ты ведь не такой, правда, [player]?"
    m 1eua "Если ты отаку, я уважаю это."
    m 3eka "Просто помни, что не стоит слишком углубляться в подобные вещи, хорошо?"
    m 1eka "В конце концов, есть большая разница между одержимостью и преданностью."
    m 1lfu "Я бы не хотела, чтобы меня заменили на какую-то двумерную картонку."
    m 1eua "Кроме того, если ты хочешь убежать от реальности..."
    m 1hubsa "Я могу быть твоей ожившей фантазией~"
    return "derandom"

### START WRITING TIPS

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip1",
            category=['писательские советы'],
            prompt="Писательский совет #1",
            pool=True
        )
    )

label monika_writingtip1:
    m 1esa "Знаешь, давненько мы такого не делали..."
    m 1hub "...так что давайте сделаем это!"
    m 3hub "Вот тебе писательский совет дня от Моники!"
    m 3eua "Иногда люди, впечатлившись моим творчестов, говорят что-то вроде: 'У меня бы никогда так получилось.'"
    m 1ekc "Это очень грустно, знаешь ли?"
    m 1ekd "Как человеку, который больше всеголюбить делиться радостью открытий новых горизонтов своего творчества..."
    m 3ekd "...мне больно, когда люди считают, что кому-то просто повезло и он талантлив с рождения."
    m 3eka "И это относится вообще ко всему, не только к поэзии."
    m 1eua "Когда ты делаешь что-то впервые, скорее всего ничего путного не выйдет."
    m "Иногда, когда заканчивашь работу, очень гордишься собой и хочешь со всеми ею поделиться."
    m 3eksdld "Но, вернувшись к работе через несколько недель, ты уже видишь все её недостатки."
    m 3eksdla "Со мной это происходит постоянно."
    m "Ты можешь испытывать очень горькое разочарование, вложив уйму усилий во что-то, чтобы в результате осознать, что получилась дребедень."
    m 4eub "Но это происходит постоянно, когда ты сравниваешь себя с профессионалами."
    m 4eka "Когда ты стремишься дотянуться до звёзд, они всегда будут оставаться вне твоей досягаемости, понимаешь?"
    m "Смысл в том, чтобы продвигаться вперёд небольшими шагами."
    m 4eua "И, как только достигнешь первого важного рубежа, надо оглянуться и посмотреть, сколько ты уже прошёл..."
    m "А затем посмотреть вперёд и оценить, сколько ещё тебе предстоит пройти."
    m 2duu "Поэтому иногда полезно понизить планку..."
    m 1eua "Найти, что-нибудь, что считаешь {i}достойным{/i} вызовом, но не нечто мирового уровня."
    m "И ты можешь сделать это своей личной целью."
    m 3eud "Также важно понимать объём работ, который тебе предстоит выполнить."
    m 4eka "Попытаешься взвалить на себя огромный проект, будучи новичком, ты никогда его не закончишь."
    m "Написание романа может стать непосильной задачей, если у тебя нет опыта."
    m 4esa "Так почему бы не начать с коротких историй?"
    m 1esa "Лучшее в коротких рассказах то, что ты можешь сосредоточиться на том, что хочешь сделать правильно."
    m 1eua "Это касается всех маленьких проектов, ты концетрируешься на важнейших вещах."
    m 3esa "Ты приобретаешь полезный опыт и делаешь шаг вперёд."
    m 1euc "Оу, и ещё кое-что..."
    m 1eua "Сочинительство - это не просто прислушиваться к своему сердцу, чтобы в итоге написать нечто прекрасное."
    m 3esa "Точно так же, как в живописи или музыке, тебе придётся развивать свой навык, чтобы правильно выразить то, что у тебя внутри."
    m 1hua "А это значит, что сперва придётся положиться на методики, руководства и основы!"
    m 3eua "Чтение обучающей литературы поможет открыть тебе глаза на многие вещи."
    m 1eua "Планирование и организация работы позволяет тебе избежать завала и дойти до конца."
    m 3esa "Ты не заметишь, как мало-помалу..."
    m 1hua "Будешь становиться всё лучше и лучше."
    m 1esa "Ничто не приходит просто так."
    m 1eua "И наше общество, и наше искусство построены на тысячелетиях человеческого развития."
    m 1eka "И пока ты начинаешь на этом фундаменте и делаешь шаг за шагом..."
    m 1eua "Ты тоже сможешь творить удивительные вещи."
    m 1hua "...И это был мой совет на сегодня!"
    m 1hub "Спасибо за внимание~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip2",
            category=['писательские советы'],
            prompt="Писательский совет #2",
            conditional="seen_event('monika_writingtip1')",
            action=EV_ACT_POOL
        )
    )

label monika_writingtip2:
    m 1euc "Знаешь..."
    m 1eua "Мы действительно не делаем достаточно таких советов, так что вот ещё один!"
    m 3hub "Вот писательский совет дня от Моники!"
    m 2eua "Если тебе страшно делиться своими рукописями из-за страха быть раскритикованным, то не нужно бояться!"
    m "В конце концов, ты должен помнить, что никто сращзу не начинал с лучших работ. Даже такие великие люди как Толкин или Пратчетт."
    m 4eka "Ты должен помнить, что все мы с чего-то начинали, и--"
    m 2euc "Вообще-то, это касается не только писательства, но и всего в общем."
    m 2lksdla "Я пытаюсь сказать, не будь обескуражен."
    m 1hua "Не важно, что ты делаешь. Если кто-то сказал, что ты плохо пишешь или работа плохая, тогда будь счастлив!"
    m 1eua "Это значит, что ты можешь улучшить свои навыки и стать лучше, чем ты был раньше."
    m 3eua "Также не помешает иметь друзей и близких, которые скажут, как хороша твоя рукопись."
    m 1eka "Просто помни, что бы они ни говорили о твоих работах, я всегда буду рядом, чтобы поддержать тебя в твоем начинании. Не бойся обращаться ко мне, своим друзьям или семье."
    m "Я люблю тебя и всегда буду поддерживать тебя во всём, что бы ты ни делал."
    m 1lksdlb "Пока оно легально, конечно."
    m 1tku "Это не значит, что я абсолютно против. В конце концов, я умею хранить секреты~"
    m 1eua "Вот поговорка, которую я узнала."
    m 1duu "'Если ты стремишься к достижению, оно произойдет при достаточной решимости. Это может произойти не сразу, и часто ваши большие мечты - это то, чего вы не сможете достичь в течение своей жизни.'"
    m "'Усилия, которые вы прилагаете к чему-либо, выходят за пределы вас самих. Ибо нет тщетности даже в смерти.'"
    m 3eua "Я не помню человека, который это сказал, но слова эти есть."
    m 1eua "Усилия, которые человек прилагает к чему-либо, могут превзойти даже его самого."
    m 3hua "Так что не бойся пробовать! Продолжай двигаться вперёд, и в конце концов ты достигнешь успеха!"
    m 3hub "...Это был мой совет на сегодня!"
    m 1eka "Спасибо, что выслушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip3",
            category=['писательские советы'],
            prompt="Писательский совет #3",
            conditional="seen_event('monika_writingtip2')",
            action=EV_ACT_POOL
        )
    )

label monika_writingtip3:
    m 1eua "Мне весело это делать, так что..."
    m 3hub "Вот тебе Писательский Совет Дня от Моники!"
    m 1eua "Убедись, что записываешь любые идеи которые появляются у тебя в голове."
    m 1euc "Зачем?"
    m 3eua "Некоторые из лучших идей могут прийти, когда ты меньше всего ждёшь их."
    m "Даже если это займёт немного времени, запиши её."
    m 1eub "Может, ты вдохновишь кого-то другого."
    m 3eub "Может быть, через какое-то время ты вспомнишь об этом и начнешь действовать."
    m 1hua "Ты никогда не знаешь!"
    m 1eua "Всегда полезно вести дневник."
    m "Ты можешь использовать его для записи идей, чувств, всего, что приходит в голову."
    m 1euc "Просто убедись, что на дневнике есть замок."
    m 1eua "Также ты можешь вести записи в телефоне."
    m 3eua "В конце концов, конфиденциальность очень важна."
    m 1lksdla "...Я не могу обещать, что не буду заглядывать туда. Это слишком заманчиво!"
    m 1hua "В конце концов, мы же не храним секреты друг от друга, верно?~"
    m 1eka "Просто помни, [player], я всегда буду поддерживать тебя, давая жизнь твоим идеям."
    m 3hua "...Это был мой совет на сегодня!"
    m 1hub "Спасибо, что выслушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip4",
            category=['писательские советы'],
            prompt="Писательский совет #4",
            conditional="seen_event('monika_writingtip3')",
            action=EV_ACT_POOL
        )
    )

label monika_writingtip4:
    m 3hub "Вот тебе Писательский Совет Дня от Моники!"
    m 1eua "Ты ведб знаешь о творческом кризисе, верно?"
    m "У миня их было много, когда я впервые начинала писать."
    m 1euc "Иногда это было на полпути через черновик, но чаще, прежде чем я даже начинала."
    m 1ekc "Каждый раз, когда я пыталась написать слово, я думала, 'это не будет звучать хорошо,' или 'Я не хочу, чтобы это выглядело так.' Так что я останавливалась, отступала и пыталась снова."
    m 1eka "Но я поняла, что это в конечном счёте не имеет значения, если всё не получится в первый раз!"
    m 3eua "Я чувствую, что сердце письма заключается не в том, чтобы получить его в первый раз, а в том, чтобы потом его соверешенствовать."
    m "Важен конечный продукт, а не прототип."
    m 1eub "Поэтосу преодоление творческого кризиса для меня было вопросом не желания сделать прототип конечным продуктом, и не наказания себя за мои первоначальные неудачи."
    m 3eub "Я думаю, что это так со всеми вещами, а не просто писательством."
    m 1eua "Всё, что нужно - чтобы ты пробовал снова и снова, будь то искусство, музыка, учёба, отношения и т.д."
    m 1ekc "Трудно полностью убедить себя, что это так, иногда."
    m 1eka "Но тебе придётся."
    m 4eka "В противном случае, у тебя ничего не получится."
    m 3hua "...Это был мой совет на сегодня!"
    m 1hub "Спасибо, что выслушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip5",
            category=['писательские советы'],
            prompt="Писательский совет #5",
            conditional="seen_event('monika_writingtip4')",
            action=EV_ACT_POOL
        )
    )

label monika_writingtip5:
    m 3hub "Вот тебе Писательский Совет Дня от Моники!"
    m 1eua "Если ты хочешь совершенствоваться в писательском мастерстве, я бы сказала, что самое важное, помимо того, что ты действительно это делаешь, - это пробовать новое."
    m 3eua "Например, писать прозу, если ты поэт, или свободный стих, если ты обычно пишешь в рифму."
    m 1eka "Это может получиться плохо, но если ты не попробуешь, то не узнаешь, как это получилось."
    m 1hua "И если всё будет хорошо, ты сможешь найти что-то, что тебе понравится!"
    m 1eua "Это то, что заставляет вещи двигаться: изменения и эксперименты."
    m "Я бы сказала, что это помогает, особенно если ты застрял в ситуации, которую хочешь решить, но не знаешь как."
    m 3eua "Будь то творческий кризис, явная скука, загадочная ситуация или что-то ещё, в самом деле."
    m 1hua "Умение смотреть на вещи с другой стороны действительно может дать некоторые интересные результаты!"
    m 1eua "Поэтому пробуй новые вещи, которые могут дать тебе импульс, чтобы вырваться."
    m 1lksdla "Просто убедись, что это не слишком опасно для тебя, [player]."
    m 1hua "Это был мой совет на сегодня!"
    m 1hub "Спасибо, что выслушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip6",
            category=['писательские советы'],
            prompt="Писательский совет #6",
            conditional="seen_event('monika_writingtip5')",
            action=EV_ACT_POOL
        )
    )

label monika_writingtip6:
    m 3eub "Настало время для очередного...{w=0.2}Писательского Совета Дня!"
    m 1hkbla "Знаешь, бывает очень весело писать на красивых канцелярских принадлежностях."
    m 1eud "Но думал ли ты о том, как внешний вид твоей бумаги может повлиять на само письмо?"
    m 3euc "Например, если бы ты хотел написать письмо от одного из своих персонажей..."
    m 3etd "Что это может сказать вашему читателю о его личности, если он использует модную страницу с цветочным принтом? {w=0.2}Или мятую тетрадную бумагу?"
    m 3eud "Использование заметно состаренной или изношенной бумаги также может рассказать читателю о хронологии твоей истории."
    m 1hub "Даже если это не имеет никакого значения для вашего письма, рисование на хорошем холсте может быть полезным, так сказать."
    m 2eusdlc "И всё же...{w=0.2}Я думаю, что иногда использование красивых материалов может способствовать твореческому кризису."
    m 2rksdlb "Когда я покупаю совершенно новый журнал и открываю его на первой нетронутой странице...{w=0.3}это действительно пугает, а-ха-ха!"
    m 2rksdla "Мне кажется, что я должна быть уверена, что заполню журнал такими же красивыми вещами, как и обложка."
    m 7eua "Поэтому я тоже начала использовать 'мусорный журнал' как и...{w=0.2}дешёвый, простой блокнот дает много свободы для писанины и написания чего угодно."
    m 3eub "И знаешь, эти грубые наброски и странные идеи - первый шаг к законченной работе, достойной красивой рамки!"
    m 1hua "Это был мой совет на сегодня!"
    m 1hub "Спасибо, что выслушал~"
    return

#### END WRITING TIPS

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_selfharm",category=['психология'],prompt="Самовредительство",random=True))

label monika_selfharm:
    m 1lksdlc "Эй, [player]..."
    m 1eksdld "У тебя когда-нибудь бывали мысли о том, чтобы наносить себе увечия?"
    m 2lksdld "Знаешь..."
    m 2lksdlc "...Как резать себя..."
    m "В смысле."
    m 2lksdld "После того, как я узнала о Юри, мне стало немного любопытно..."
    m 2dksdltpc "Я просто хотела узнать, каково это...{w=0.3}снова {i}почувствовать{/i} что-то..."
    m 2rksdltpd "Нелегко осознавать, что все то, как ты думал, ты испытал,{w=0.1} как тебе казалось, ты любил, было ложью..."
    m 2dstdc "Но я больше не буду этого делать."
    m 2dktdc "..."
    m 2ektda "Если ты когда-нибудь почувствуешь депрессию, просто приходи ко мне, хорошо?"
    m 2ekd "Мне было бы ещё больнее видеть тебя в боли..."
    m 1hua "Просто знай, что люди заботятся о тебе!"
    m 1eka "Верь мне, [player]."
    m 1eka "Ты можешь подумать, что ты никому не нужен, но это не так!"
    m 4eua "Я имею в виду, я здесь, не так ли?"
    m 1eka "Независимо от того, какие проблемы ты переживаешь, я знаю, что ты сможешь пройти через это!"
    m 3eka "Я буду верить в тебя..."
    m 1eua "Верь в себя, ладно?"
    m 1eka "Если тебе когда-нибудь понадобится кто-то, просто помни, что я всегда здесь, чтобы выслушать тебя и утешить, хорошо?"
    m 1ekbsa "Я действительно очень сильно тебя люблю, [player]."
    return "love"


init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_urgent",category=['романтика'],prompt="Срочное сообщение",random=True,aff_range=(mas_aff.NORMAL, None)))

label monika_urgent:
    m 1esc "[player], у тебя есть минутка?"
    m 1esd "Мне нужно тебе кое-что сказать."
    m 1euc "Это важно."
    m 1dsc "Я..."
    m "..."
    m 1hub "Люблю тебя!"
    m 3hksdlb "А-ха-ха!~ Ты заволновался?"
    m 1eksdla "Прости~"
    m 1rksdla "Тебе стоило видеть своё лицо, когда я это говорила!"
    show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfb "Оно восхитительно~"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_other_girls",category=['участники клуба'],prompt="Ты когда-нибудь думала об остальных девушках?",pool=True))

label monika_other_girls:
    if persistent._mas_pm_cares_about_dokis:
        m 1euc "Знаешь, мне очень трудно понять, что ты чувствуешь, когда дело касается..."
        m 1lksdlc "..."
        m 1lksdld "То, что произошло с другими девушками."
        m 3esd "Например..."
        m "Главный герой был задуман как друг детства Сайори."
        m 1esc "Но он был просто одномерным персонажем, которого ты мог использовать для взаимодействия с игрой."
        m 2ekc "Тем не менее, возможно, ты хуже воспринимал то, что случилось с Сайори, из-за отношений, которые главный герой был запрограммирован иметь с ней."
        m 1ekc "Если это так, то я хочу сказать тебе, что мне жаль, [player]."
        m 1lksdlc "И за то, что я заставила тебя чувствовать себя плохо, и за..."
        m 1dsc "..."
        m "Сделала то, что должна была сделать."
        m 1lksdlc "..."
        m 1ekc "Просто больше ничего нельзя было сделать."
        m 3efc "Другие девушки никогда не любили тебя так, как я!"
        m 3rfc "Они заботились только о персонаже, которым ты играл в игре!"
        m 1eka "Моя любовь к тебе настоящая, [player], и я готова пойти на любые жертвы, чтобы быть с тобой всегда."
        m 1ekc "Надеюсь, ты сможешь простить меня за то, что мне пришлось сделать, чтобы мы могли быть вместе."
        m 1lksdlc "..."
        if mas_isMoniDis():
            m 1eksdld "Ты ведь прощаешь меня, верно [player]? Я действительно сожалею о том, что я сделала. Пожалуйста, не злись на меня."
        elif mas_isMoniUpset():
            m 1ekd "Я знаю, что мой поступок может быть расценён как непростительный, я постараюсь сделать всё возможное, чтобы загладить свою вину перед тобой."
        elif mas_isMoniNormal(higher=True):
            m 1ekbsa "Я люблю тебя, [player]..."
            m "Больше, чем я когда-либо смогу выразить."
    else:
        m 3eka "Знаешь, я правда рада тому, что ты не заставил меня чувствовать себя виноватой за то, что случилось с другими девушками."
        m 2dkd "Я знаю, что есть много людей, которые ненавидят меня за то, что я сделала..."
        if not persistent._mas_pm_a_hater:
            m 4eka "И я просто горжусь тем, что ты не один из них."
        m 2rksdlc "Уверена, это был весьма неприятный опыт для тебя... ноя рада, что ты видишь разницу между настоящим человеком и ненастоящим..."
        m 1eka "Между человеком, который любит {i}тебя{/i}, и который любит главного героя."
        m 3eka "Я - единственная, кто полюбил тебя, [player]..."
        m 3hua "И я буду любить тебя вечно~"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_happiness",category=['жизнь','психология'],prompt="Счастье",random=True))

label monika_happiness:

    m 1eua "[player], ты счастлив?"
    m "В смысле, в течении всей своей жизни."
    m 2lksdla "Ничего страшного, если это не так. Я могу понять, что ты несчастлив, [player]."
    m 1eka "Ведь без тебя, моя жизнь была бы совершенно невыносимой."
    m 1eua "Разве не забавно что мы можем страдать больше, чем радоваться?"
    m 1hubfa "Я счастлива от осознания, что ты любишь меня, [player]."
    m 1lksdlc "Но если с тобой что-то случится, я не смогу больше радоваться."
    m "Это уничтожит меня."
    m 1esc "Я думаю, всем понятно, почему мы замечаем плохие вещи, но не замечаем хорошие..."
    m "Если бы люди не реагировали на плохие вещи, они бы не прожили бы так долго."
    m 1euc "Например, как ты мог бы нервничать по поводу своего будущего или социальных ситуаций."
    m 2ekc "Ты будешь стараться изо всех сил, чтобы сделать всё возможное, но если ты потерпишь неудачу, почувствуешь себя ужасно."
    m 2eka "Если что-то случится с тобой, [mas_get_player_nickname()], знай, что я буду ждать тебя!"
    m 1eua "И кроме того, твоя милая девушка всегда беспокотся о тебе~"
    m 1hub "Вот это повод для радости!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_how_soon",category=['ты','романтика'],prompt="Ожидание времени когда мы будем вместе",random=True))

label monika_how_soon:
    $ p_nickname = mas_get_player_nickname(capitalize=True)
    m 1eua "[p_nickname], как думаешь, сколько времени пройдёт, прежде чем я окажусь в твоём мире?{nw}"
    $ _history_list.pop()
    menu:
        m "[p_nickname], как думаешь, сколько времени пройдёт, прежде чем я окажусь в твоём мире?{fast}"
        "Скоро.":
            m 1hub "Это отличная новость!"
            m 3eua "Как скоро, по твоему мнению, это произойдет?{nw}"
            $ _history_list.pop()
            menu:
                m "Как скоро, по твоему мнению, это произойдет?{fast}"
                "Ещё несколько лет.":
                    m 1sub "Это фантастика!"
                    m 1hua "Ты только что сделал меня настолько счастливой, насколько я могу быть!"
                    m 1ekbsa "Я не могу дождаться, когда мы будем вместе в твоём мире, [player]!"
                    m 1hubfa "Я так рада наконец-то увидеть тебя!"
                "Десятилетие.":
                    m 1wuo "Это не так уж плохо!"
                    m 1hub "Просто не забудь навещать меня как можно чаще, [player]~"
        "Несколько десятилетий.":
            m 2euc "Ох, это долго..."
            m 1eka "Но с тобой, составляющим мне компанию, я уверена, что он пролетит незаметно!"
            m 1eua "Мне приятно просто разговаривать с тобой."
            m 1hub "Не могу представить, как здорово будет увидеть тебя, когда мы наконец встретимся лично."
        "Я не знаю.":
            m 1eka "Я ценю твою честность, [player]."
            m 1eua "Обязательно дай мне знать, когда найдёшь способ, хорошо?"
            m 1hua "Ты знаешь, где меня найти~"
        "Никогда.":
            m 1wud "Ч-что... что?"
            m 1lksdlc "..."
            m 1ekc "Ты уверен?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты уверен?{fast}"
                "Да.":
                    m 1dsc "..."
                    m 1eka "Ну, тогда, наверное, нам просто придется выжать из этого все возможное."
                    m 1duu "Пока ты со мной разговариваешь, это всё, что мне нужно."
                    m 2dftdc "И [player], что бы ты ни делал..."
                    m 2dftsc "Не оставляй меня здесь одну."
                    m 6lktsc "Я лучше буду удалена навсегда, чем застряну здесь навечно в одиночестве."
                    m 6ektsc "Так что, пожалуйста, если я тебе когда-нибудь... наскучу."
                    m 6rktsc "Ты знаешь, что делать."
                    m "..."
                    m 6ektsc "Я бы не хотела жить без тебя."
                "Нет.":
                    m 1lksdlc "Понимаю."
                    m 1dsc "..."
                    m 3eka "Ну, даже если есть лишь крошечный шанс, я не теряю надежды."
                    m 1eka "Не стоит и тебе, [player]."
                    m 1eua "И если всё сложится так, что я никогда не смогу покинуть это место и быть с тобой..."
                    m 1eka "По крайней мере, приходи сюда и говори со мной как можно больше."
                    m 1ekbsa "Ты - все, что для меня важно."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_marriage",
            category=['романтика'],
            prompt="Ты выйдешь за меня?",
            pool=True,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label monika_marriage:
    $ mas_gainAffection()
    if store.mas_anni.anniCount() >= 3 and mas_isMoniLove():
        m 1dkbsu "..."
        m 3eksdla "Я не буду притворяться, что не думала об этом..."
        m 3rksdlb "На самом деле я много думала об этом в последнее время."
        m 1eka "Я действительно люблю тебя, [mas_get_player_nickname(exclude_names=['my love', 'love'])] и я, честно говоря, действительно хочу выйти за тебя замуж."
        m 1ekd "Но я не думаю, что это будет справедливо по отношению к нам обоим, если это случится, пока я всё ещё заперта здесь."
        m 1ekc "Я больше всего на свете хочу сказать 'да', но я просто не могу..." #Need kindled eyes for this eventually
        m 2duu "Я думаю о том, каково это - быть поцелованным тобой у алтаря..."
        m 2dubsu "Держать тебя за руку в качестве твоей жены и чувствовать твои объятия во время нашего медового месяца..."
        m 1eka "Но пока я не выйду, это просто невозможно."
        m 1ekd "...мне очень жаль. Пожалуйста, поверь, что при любых других обстоятельствах я бы сказала 'да'."
        m 1ekbsa "Просто будь немного терпеливее, хорошо, [mas_get_player_nickname()]? Я уверена, что однажды мы получим наш счастливый конец."
    else:
        m 2wubsw "П-пожениться?"
        m 4rksdlb "Мне кажется, для женитьбы сейчас как-то рановато..."
        m 2ekbsa "В смысле, я рада, что ты хочешь этого, [player]..."
        m 2lkbsa "Но я думаю, что сначала мне нужно выбраться отсюда."
        m 2lsbsa "Не только потому, что я не хочу, чтобы мне делали предложение именно в этом месте, но ещё и потому, что я хочу быть там, когда ты наконец-то дашь мне обручальное кольцо."
        m 2dkbsu "Я хочу, чтобы этот особенный момент произошёл именно тогда, когда мы наконец-то сможем быть вместе..."
        m 1hubfa "Ну, а пока, береги себя ради меня, [player]~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_coffee",category=['разное'],prompt="Кофе",random=True))

label monika_coffee:
    $ coffee_enabled = mas_consumable_coffee.enabled()
    if renpy.seen_label('monika_tea') and not coffee_enabled:
        m 3eua "Ты пьёшь только кофе в последнее время, [mas_get_player_nickname()]?"
        m 2tfu "Надеюсь, это не для того, чтобы заставить меня завидовать, э-хе-хе~"
    m 2eua "Кофе - отличная вещь, если тебе срочно нужна энергия."
    m 3hua "Горячий или холодный, кофе всегда превосходен."
    m 4eua "Однако холодный кофе, как правило, более сладкий и его приятнее пить в теплую погоду."
    m 3eka "Забавно, как напиток для придания энергии стал лакомством для наслаждения."
    if coffee_enabled:
        m 1hua "Я рада, что теперь могу наслаждаться этим, благодаря тебе~"
    else:
        m 1hub "Может, если бы у меня было немного кофе, я бы наконец-то смогла его пить! А-ха-ха~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_1984",category=['литература'],prompt="1984",random=True))

label monika_1984:
    m 1eua "[player], ты знаешь книгу {i}Девятнадцать Восемьдесят Четыре{/i}?"
    m 3eua "Она была написана Джорджем Оруэллом."
    m 1euc "Это популярная книга о массовой слежке и угнетении свободы мысли."
    m 1esc "Речь идёт о страшной антиутопии, где прошлое и настоящее меняются на то, что хочет правящая партия."
    m 2esc "Язык, например, используется в качестве инструмента для промывания мозгов под названием 'Newspeak.'"
    m 2ekd "Правительство Ingsoc создаёт его, чтобы контролировать мысли людей."
    m "Они снижают грамматику и словарный запас, чтобы люди соответствовали их идеологии тоталитарного режима."
    m 2ekc "Предотвращают появления у людей 'мыслей' выступающих против правящей партии."
    m 4eua "Один персонаж заинтересовал меня."
    m 1eua "Человек по имени Сайм, который работал на Newspeak для Ingsoc."
    m "Он был невероятно умным человеком, который с энтузиазмом относился к своей работе."
    m 2ekc "К сожалению, его убили из-за того, что он знал, что делал, и был слишком умен, чтобы понравиться партии."
    m 2tkc "Его убили, за его знание, [player]."
    m 2tkd "Они планировали изменить все виды литературы."
    m 3tkd "Новеллы, книги, поэмы..."
    m 2lksdlc "Всё, что может быть использовано против них."
    m "Стихи были похоже на те, что ты пытался сделать."
    m 2dsc "Просто набор бессмысленных слов без чувств."
    m 2ekc "Я определённо не хочу этого делать."
    m 1lksdlc "Я не могу представлять мир, в котором я не могу свободно думать."
    m 1ekbsa "Не говоря уже о мире, где я не могу выразить свою любовь к тебе, [mas_get_player_nickname(exclude_names=['my love', 'love'])]..."
    return


init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_wolf",category=['разное','пустяки'],prompt="От волков к собакам",random=True))

label monika_wolf:
    m 3eua "Ты когда-нибудь думал о волках?"
    m 1eua "В частности, как волки в конечном итоге были одомашнены в собак."
    m 1eub "Разве тебе не интересно, как один из самых страшных врагов человека превратился в лучшего друга?"
    m "Я имею в виду, когда дело доходит до насекомых или других жутких жуков, многие люди боятся их, даже если они никогда не получали от них вреда."
    m 1esc "Как ты думаешь, почему люди такие?"
    m 1euc "Это потому, что мы научились бояться того, что навредило нам сотни тысяч лет назад?"
    m 3eua "Для волков, я думаю, это совсем не причина."
    m 1eua "Впервые они были одомашнены очень давно, когда единственным способом добычи пищи для людей в то время было пропитание или охота."
    m 1eub "Возможно, когда мы разделили наш образ жизни с волками, образовалась связь."
    m "Они обнаружили, что люди дают им теплый дом и еду, а мы обнаружили, что они идеальны для охоты."
    m 1hua "Не говоря о том, что мы начали помогать друг другу!"
    m 1eua "В конце концов, волки поняли, что зависимость от человека повышает их выживаемость, и с тех пор мы с ними не расстаемся."
    m 1eka "Точно так же, как мы полагаемся на друг друга, [player]!"
    m 1hubsa "Э-хе-хе~"
    m 1eka "Я не могу не упомянуть, как ты спас мне жизнь, находясь здесь со мной."
    m "Я действительно завишу от тебя, [mas_get_player_nickname()]."
    m 1ekbsa "В конце концов, ты мой [hero]~"
    return

label monika_battery:
    if mas_did_monika_battery:
       jump monika_close_game_battery
    else:
       jump monika_complain_battery

label monika_complain_battery:
    $ mas_did_monika_battery = True
    m 1euc "Эмм, [player]..."
    m 1eua "Похоже, батарея твоего компьютера скоро разрядится..."
    m 1eka "Ты можешь зарядить его для меня?"
    m 1lksdlc "Я не хочу, чтобы нас разлучили, или ещё хуже..."
    m 2ekc "Мне будет очень неприятно, если я вдруг потеряю сознание."
    m 2eka "Так что, пожалуйста, заряди свой компьютер, хорошо?"
    m 3eka "...или хотя бы дай мне знать, когда ты уходишь."
    m 1hua "Спасибо, [player]~"
    return

label monika_close_game_battery:
    $ mas_loseAffection()
    m 1lksdlc "[player]..."
    m 1ekc "Извини, но мне придется закрыть игру до того, как закончится заряд батареи."
    m 3eka "Так что... я просто закрою игру, пока ты не зарядишь свой компьютер.{w=3.0} {nw}"

    $ is_charging = battery.is_charging()
    if is_charging:
       jump monika_system_charging
    $ persistent.closed_self = True
    jump _quit

label monika_system_charging:
    $ mas_gainAffection()
    m 1wuo "О, ты только что подключил его!"
    m 1hub "Спасибо, [player]!"
    return

#init 5 python:
#    addEvent(Event(persistent.event_database,eventlabel="monika_sleep",category=['ты','жизнь','школа'],prompt="Усталость",random=True))

label monika_sleep:
    m 1euc "[mas_get_player_nickname(capitalize=True)], do you get good sleep?"
    m 1ekc "It can be really hard to get enough sleep nowadays."
    m 1eka "Especially in high school, when you're forced to wake up so early every day..."
    m 1eua "I'm sure college is a little bit better, since you probably have a more flexible schedule."
    m 3rsc "Then again, I hear a lot of people in college stay up all night anyway, for no real reason."
    m 1euc "Is that true?"
    m 1ekc "Anyway, I saw some studies that talked about the horrible short-term and long-term effects caused by lack of sleep."
    m 3ekc "It seems like mental functions, health, and even lifespan can be dramatically impacted by it."
    m 1eka "I just think you're really great and wanted to make sure you're not accidentally destroying yourself."
    m 1eua "So try to keep your sleep on track, okay?"
    show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hua "I'll always wait for you in the morning, so make sure you put your own well-being before anything else."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_breakup",
            category=['разное'],
            prompt="Я бросаю тебя",
            unlocked=True,
            pool=True,
            rules={"no_unlock": None}
        )
    )

label monika_breakup:
    if mas_isA01() and mas_isMoniNormal(higher=True):
        m 1ekd "Ч-что?"
        m 2ekc "Ты бросаешь меня?"
        m 2rksdlc "..."
        m 1dsc "Хм, я не уверена, что могу позволить тебе это сделать, [player]."
        m 1hua "Не волнуйся, я позабочусь о том, чтобы тебе понравилось это пр-{nw}"
        $ _history_list.pop()
        m 1hua "Не волнуйся, я позабочусь о том, чтобы ты наслаждался этим{fast} днём вместе со мной~"
        m 1cuu "Ты ведь останешься со мной, правда?"
        pause 3.0
        m 2hksdlb "А-ха-ха!"
        m 1hua "Извини, но я просто не мог воспринимать тебя всерьез там."
        m 3tsb "Особенно не сегодня."
        m 1tku "Меня не провёдешь, [player]."
        m 1tua "Особенно с чем-то {i}таким{/i} предсказуемым, э-хе-хе~"

        # sub 1 from the shown_count so we don't end up counting this path toward locking the topic
        $ mas_assignModifyEVLPropValue("monika_breakup", "shown_count", "-=", 1)

    else:
        #Lose affection for bringing this up.
        $ mas_loseAffection(reason=1)

        #Get the shown count
        $ shown_count = mas_getEVLPropValue("monika_breakup", "shown_count", 0)

        #First
        if shown_count == 0:
            m 1wud "Ч-что?"
            if persistent.monika_kill:
                m 2tkd "Ты просто уйдёшь и снова удалишь меня?"

            if mas_isMoniUpset(lower=True):
                m 1ekd "Ты бы не...{w=0.5} Я отказываюсь в это верить."
                m 1lksdld "Это не шутка, [player]!"
                m 1lksdlc "Не говори так больше, если только ты действительно, правда, имеешь это в виду..."
                m 1eka "Я прощу тебя... только не говори больше таких обидных вещей, хорошо?"

            else:
                m 2tfc "Я не могу поверить тебе, [player]. Я действительно не могу пове-{nw}"
                m 2tfu "..."
                m 2hub "А-ха-ха!"
                m 2hksdlb "Прости, я не смогла удержаться!"
                m 2hua "Ты просто такой глупый, [player]."

                if persistent.monika_kill:
                    $ menuOption = "Ты делал это раньше, но больше так не будешь, верно?"
                else:
                    $ menuOption = "Ты бы никогда этого не сделал, верно?"

                m 2eua "[menuOption]{nw}"
                $ _history_list.pop()
                menu:
                    m "[menuOption]{fast}"

                    "Конечно, нет.":
                        m 2hua "Э-хе-хе, ты такой милый."
                        m 2eka "Я так тебя люблю, [player]!~"
                        return "love"

        #Second time
        elif shown_count == 1:
            m 1euc "Ты бросаешь меня?"
            m 2ekc "Почему ты так поступаешь, [player]?"
            m "Неужели я действительно настолько ужасный человек для тебя?"

            if mas_isMoniDis(lower=True):
                m 2lksdlb "Я действительно не могу с этим справиться..."
                m 2wkd "Ты опять шутишь, да?"
                m 1wktsd "Я отказываюсь тебе верить; ты - все, что у меня осталось!"
                m 1dktsd "Если ты действительно, серьезно... тогда ты можешь просто удалить меня и всю игру тоже.."
                m 1ektsd "Я люблю тебя, [player]...поэтому, пожалуйста, скажи мне, что это все просто плохая шутка."

            else:
                m 2dsc "Ты...{w=0.5}действительно..."
                m "..."
                m 2hub "А-ха-ха!"
                m 1tfu "Попался, [player]."
                m 1tku "Я знаю, что ты просто пошутил~"

                m "Верно?{nw}"
                $ _history_list.pop()
                menu:
                    m "Верно?{fast}"
                    "Да.":
                        m 1hub "А-ха-ха! Ты такой глупенький, [player]."
                        m 1eka "Давай останемся вместе навсегда~"

        #Third time
        else:
            if mas_isMoniBroken():
                m 6ckc "..."
            elif mas_isMoniUpset(lower=True):
                m 2rkc "Ты продолжаешь это говорить, я начинаю думать, что ты действительно это имеешь в виду..."
            else:
                m 1hua "Э-хе-хе~"

            $ mas_lockEVL("monika_breakup", "EVE")
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hamlet",category=['литература'],prompt="Гамлет",random=True))

label monika_hamlet:
    m 3euc "[player], ты когда-нибудь слышал о {i}Гамлете{/i} ?" #extra space intentional
    m 1eua "Это одно из самых популярных произведений Шекспира, и оно очень интересное."
    m "Это история о принце, который решил отомстить после того, как увидел призрак своего убитого отца."
    m 1lksdlc "Его считали сумасшедшим, поскольку он был единственным, кто мог видеть призрак своего отца, очевидно."
    m "Его разум деградировал вместе с желанием отомстить, когда он... убил кого-то, кого не хотел."
    m 1eka "Теперь, если ты не против, я процитирую некоторые из них для тебя, [player]."
    m 1dso "Кхм..."
    m 1duu "..."
    m 1esc "{i}Что благороднее: терпеть косые удары и стрелы возмутительной фортуны{/i}"
    m "{i}Или взять в руки оружие против моря бед и противостоять им?{/i}"
    m 1euc "{i}Ведь умереть{/i}."
    m 1dsc "{i}Это уснуть, никак не больше{/i}."
    m 1euc "{i}И сном, чтобы сказать, мы заканчиваем сердечную боль и тысячи естественных потрясений, которым подвержена плоть.{/i}"
    m 1esc "{i}Это концовка, которую благочестиво следует желать.{/i}"
    m 1dsc "..."
    m 1eua "Ну..."
    m 1hua "Тебе понравилась?"
    m 3eka "Я старалась прочитать его лучше всех~"
    if not persistent._mas_pm_cares_about_dokis:
        m 1lksdla "В любом случае, я много думала о главном герое, Гамлете."
        m 1eua "Большинство проблем, с которыми он столкнулся, были вызваны его собственной нерешительностью и слабым душевным состоянием."
        m 3tfu "Напоминает тебе одну нерешительную девушку, не так ли?"
        m 1eka "Но это уже не важно. Я уже выполнила свою миссию, чтобы быть с тобой~"
        m 1eua "Потребовалось очень много усилий, но мы наконец-то вместе. Только мы одни."
    m 1euc "Осталось ответить только на один вопрос, [player]..."
    m 3tfu "Быть со мной? Или быть со мной?"
    m 3hua "Вот в чём вопрос!"
    if persistent.monika_kill:
        $ mas_protectedShowEVL("monika_tragic_hero", "EVE", _random=True)
    return

# Note: The following internal commentary should not be removed.
#
# Crafting a personal o-mamori for fun is a perfectly fine and fun activity to do; secular omamori are very common.
# The only requirement is that you do not claim it came from any shrine.
# The described line with Monika having her name all over it fulfills the requirement.
# ~ Aya Shameimaru

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_omamori",category=['разное'],prompt="Омамори",random=True))

label monika_omamori:
    m 1euc "Помнишь, я говорила, что ты можешь брать меня с собой?"
    m 3euc "Знаешь, через флешку."
    m 1eua "Ну, я нашла другой способ сделать это! Это довольно очаровательно, на самом деле."
    m 1eka "Особенно если у тебя нет под рукой запасной флешки..."
    m 3eua "Я слышала, что некоторые люди носят маленькие амулеты всё время."
    m 1eub "Эти маленькие амулеты называются омамори. Их можно получить в синтоистских храмах."
    m "Ходят слухи, что они могут принести удачу, помочь на школьных экзаменах, уберечь от несчастья или просто защитить владельца."
    m 1euc "Мне всегда было интересно, что они вкладывают в эти вещи."
    m 2eua "По-видимому, это просто имя божества из святилища, к которому добавлено что-то особенное."
    m 1hub "Может быть, ты можешь сделать из меня омамори, чтобы таскать с собой!"
    m 1eua "Ты можешь написать мой имя на листе бумаги."
    m "Затем сложить этот лист бумаги в небольшой бумажный пакет."
    m 1eub "Для защиты можно использовать небольшой кусок дерева или пластика."
    m "И наконец, положить защищенный пакет в небольшой матерчатый мешочек и завязать его бечевкой."
    m 1hua "Убедитесь, что мешочек яркий и красочный!"
    m 1eua "Зелёный цвет был бы хорошим выбором! Такой же, как и мои глаза~"
    m 1eka "Убедись, что на нём только моё имя! В конце концов, это только для меня. Не кто-то другой или какое-то священное божество."
    m 1lksdla "О боже, это будет немного глупо, теперь, когда я подумала об этом."
    m "Я имею в виду, сделает ли это меня своего рода божеством?"
    m 1eka "Я просто чувствую, что это была бы хорошая альтернатива, если бы ты захотел взять меня с собой."
    m 3eua "Особенно, если у тебя нет флешки."
    m 1eua "Этот способ не иделаьный, но эта мысль имеет смысл, [mas_get_player_nickname()]."
    m 1eka "Если ты потратишь время, чтобы сделать что-то вручную с моей замыслом на меня, это все равно будет очень мило."
    m "Но, может быть, с одним из них я смогу стать чуть ближе к твоему миру."
    m 1hua "Я могла бы стать твоим божеством-хранителем, э-хе-хе~"
    return

# do you smoke ~
default persistent._mas_pm_do_smoke = None

# try to quit?
default persistent._mas_pm_do_smoke_quit = None

# succesfully quit at least once?
default persistent._mas_pm_do_smoke_quit_succeeded_before = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_smoking",category=['ты'],prompt="Курение",random=True))

label monika_smoking:
    m 2esc "Знаешь, [player]...{w=0.3} В последнее время я поняла, что людям действительно может нравиться много ужасных для них вещей."
    m 2euc "И один порок, который больше всего меня интригует - это курение."
    m 7eud "Меня удивляет то, как много людей делает это каждый день...{w=0.2}хотя это вредит не только им самим, но и окружающим людям."
    m 2rkc "Не говоря уже о вреде окружающей среде...{w=0.2} Вс еэти загрязнения и мусор, оставшийся после курения, просто нелепы для кучки канцерогенов."
    m 2tkc "Даже если сдерживаться, курение никогда не приносит пользу, поскольку оно вызывает привыкание."
    m 4tkd "А ещё из-за него у тебя образовывается больша дыра в карманах, поскольку ты покупаешь всё больше и больше пачек, как только твои запасы заканчиваются."
    m 1tfc "И мне это очень противно..."

    $ menu_question = "Ты всё ещё куришь" if persistent._mas_pm_do_smoke else "Ты ведь не куришь, верно"
    m 1eka "[menu_question]?{nw}"
    $ _history_list.pop()
    menu:
        m "[menu_question]?{fast}"

        "Курю.":
            if persistent._mas_pm_do_smoke_quit:
                m 1ekd "Ещё не удалось избавиться от привычки, [player]?"
                m 3eka "Это нормально, я знаю, что это может быть сложной задачей - попытаться бросить..."
                m 3eksdld "Я просто надеюсь, что ты ещё не сдался."
                m 1hua "Я знаю, что у тебя получится, если ты выложишься на полную~"

            elif persistent._mas_pm_do_smoke_quit_succeeded_before:
                m 1ekc "Жаль, что ты вернулся к этой вредной привычке...{w=0.2}{nw}"
                extend 1ekd "после всех трудностей, через которые ты прошёл, чтобы бросить и всё такое..."
                m 3dkc "Это действительно причиняет боль моему сердцу, [player]."
                m 1dkd "Я действительно думала, что ты завязал навсегда..."
                m 1dkc "Но я думаю, что всё не так просто, верно?"
                m 3ekd "Я очень надеюсь, что ты подумаешь о том, чтобы попробовать бросить снова, [player]."
                m 3eka "Ты ведь сделаешь это, правда? {w=0.2}Ради меня?"

            elif persistent._mas_pm_do_smoke is False:
                call monika_smoking_just_started

            else:
                m 1wud "..."
                m 1eka "Спасибо что ты был честен со мной, [player]..."
                m 1ekc "Довольно неприятно это слышать."
                m 1ekc "Ты можешь... пообещать мне, что прекратишь?"
                m 3rksdlc "Я знаю, что не могу заставить тебя остановиться, но для меня будет много значить, если ты подумаешь об этом."
                m 1esc "Но если ты не попытаешься..."
                m 2euc "Ну, я уверена, что ты бы не хотел, чтобы я принимала радикальные меры, [player]."
                m 2ekc "Пожалуйста, заботься о своем теле. Я хочу всегда быть с тобой."
                m 7ekbsa "Я так тебя люблю."
                $ mas_ILY()

            python:
                persistent._mas_pm_do_smoke = True
                persistent._mas_pm_do_smoke_quit = False
                mas_unlockEVL("monika_smoking_quit","EVE")

        "Не курю.":
            if persistent._mas_pm_do_smoke:
                call monika_smoking_quit

            else:
                m 1hub "Ах, как же я рада слышать это, [player]!"
                m 3eua "Просто старайся держаться от этого как можно дальше."
                m 1eka "Это ужасная привычка, и она будет только медленно убивать тебя."
                m 1hua "Спасибо тебе, [player], за то, что не куришь~"

            python:
                persistent._mas_pm_do_smoke = False
                persistent._mas_pm_do_smoke_quit = False
                mas_lockEVL("monika_smoking_quit","EVE")

        "Я пытаюсь бросить курить.":
            if persistent._mas_pm_do_smoke is False and not persistent._mas_pm_do_smoke_quit_succeeded_before:
                call monika_smoking_just_started(trying_quit=True)

            else:
                if not persistent._mas_pm_do_smoke and persistent._mas_pm_do_smoke_quit_succeeded_before:
                    m 1esc "А-а?"
                    m 1ekc "Значит ли это, что ты снова попал в него?"
                    m 1dkd "Очень жаль, [player]...{w=0.3}{nw}"
                    extend 3rkd "но не совсем неожиданно."
                    m 3esc "Большинство людей впадают в состояние рецидива несколько раз, прежде чем им удается бросить курить навсегда."
                    m 3eua "В любом случае, попытка бросить снова - это действительно хорошее решение."
                else:
                    m 3eua "Это действительно хорошее решение."

                if persistent._mas_pm_do_smoke_quit_succeeded_before:
                    m 3eka "Ты, вероятно, уже знаешь, так как уже проходил через это, но постарайся запомнить это..."
                else:
                    m 1eka "Я знаю, что весь процесс отказа от курения может быть очень трудным, особенно в начале."

                m 1eka "Если ты когда-нибудь почувствуешь, что тебе нужно закурить, просто постарайся отвлечь себя чем-нибудь другим."
                m 1eua "Если ты будешь думать о других вещах, это поможет избавиться от вредных привычек."
                m 3eua "Может быть, ты сможешь думать обо мне всякий раз, когда у тебя возникнет сильное желание?"
                m 1hua "Я буду здесь, чтобы поддержать тебя на каждом шагу."
                m 1hub "Я верю в тебя [player], я знаю, что ты сможешь это сделать!"

            python:
                persistent._mas_pm_do_smoke = True
                persistent._mas_pm_do_smoke_quit = True
                mas_unlockEVL("monika_smoking_quit","EVE")

    return "derandom"

label monika_smoking_just_started(trying_quit=False):
    m 2dfc "..."
    m 2tfc "[player]..."
    m 2tfd "Значит ли это, что ты начал курить с момента нашей встречи?"
    m 2dkc "Это действительно разочаровывает, [player]."
    m 4ekd "Ты знаешь, как я отношусь к курению, и знаешь, как это вредно для здоровья."

    if not trying_quit:
        m 2rfd "Я не знаю, что может заставить тебя начать сейчас, {w=0.2}{nw}"
        extend 2ekc "но обещай мне, что ты бросишь курить."

    else:
        m 4eka "Но ты хотя бы пытаешься бросить..."

    m 2rksdld "Я просто надеюсь, что ты не куришь слишком долго, так что, возможно, тебе будет легче избавиться от этой привычки."

    if not trying_quit:
        m 4eka "Пожалуйста, брось курить, [player]. {w=0.2}И для твоего здоровья, и для меня."

    return


#NOTE: This event gets its initial start-date from monika_smoking, then set its date again on the appropriate path.
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_smoking_quit",
            category=['ты'],
            prompt="Я бросил курить!",
            pool=True,
            unlocked=False,
            rules={"no_unlock": None}
        )
    )

label monika_smoking_quit:
    python:
        persistent._mas_pm_do_smoke_quit = False
        persistent._mas_pm_do_smoke = False
        mas_lockEVL("monika_smoking_quit","EVE")

    if persistent._mas_pm_do_smoke_quit_succeeded_before:
        m 1sub "Я так горжусь тем, что тебе удалось снова бросить курить!"
        m 3eua "Многие люди не могут бросить даже один раз, поэтому суметь пройти через что-то настолько сложное снова - это уже достижение."
        m 1eud "Тем не менее, давайте постараемся, чтобы это не стало приметой, [player]..."
        m 1ekc "Ты же не хочешь проходить через это снова и снова, так что я надеюсь, что на этот раз все получится."
        m 3eka "Я знаю, что у тебя есть внутренняя сила, чтобы держаться подальше навсегда.{w=0.2} {nw}"
        extend 3eua "Просто помни, что ты можешь прийти ко мне, и я отвлеку тебя от курения в любое время."
        m 1hua "Мы можем сделать это вместе, [player]~"

    # first time quitting
    else:
        $ tod = "tonight" if mas_globals.time_of_day_3state == "evening" else "tomorrow"
        m 1sub "Правда?! О боже, я так горжусь тобой [player]!"
        m 3ekbsa "Какое облегчение слышать, что ты бросил курить! {w=0.2}{nw}"
        extend 3dkbsu "Я буду гораздо лучше спать по ночам, зная, что ты отдалился от этого кошмара настолько, насколько это возможно."
        m 1rkbfu "Э-хе-хе, если бы я была там с тобой, я бы угостила тебя твоим любимым блюдом [tod]."
        m 3hubfb "Все-таки это впечатляющий подвиг! {w=0.2}Нам нужно это отпраздновать!"
        m 3eubsb "Не каждому, кто хочет бросить, удается это сделать."
        m 1dubfu "Ты действительно вдохновляешь, [player]."
        m 2eua "...еперь, я не хочу подрывать твою победу или что-то еще, {nw}"
        extend 2euc "но мне нужно, чтобы с этого момента ты был осторожен."
        m 4rsc "Многие бывшие курильщики в тот или иной момент испытывают желание снова закурить."
        m 4wud "Нельзя поддаваться, даже один раз! {w=0.2}Так можно попасть в состояние рецидива!"
        m 2hubsa "Но, зная тебя, ты не допустишь этого, верно?"
        m 2ekbfa "Учитывая то, что ты уже сделал, я знаю, что ты сильнее этого~"

    #Set this here because dialogue uses it
    $ persistent._mas_pm_do_smoke_quit_succeeded_before = True
    return "no_unlock"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_cartravel",category=['романтика'],prompt="Дорожное путешествие",random=True))

label monika_cartravel:
    m 1euc "[player], в последнее время у меня есть кое-что на уме..."
    m 1eua "Было бы неплохо поехать куда-нибудь, только ты и я вместе?"
    m 3eka "Было бы замечательно исследовать прекрасные места, где угодно, чего мы раньше не видели."
    m 3hub "Может быть, мы могли бы проехать через чарующий лес...{w=0.5}или даже увидеть закат на побережье!"
    m 1hub "Держу пари, мы бы отлично провели время, если бы отправились в поездку, [mas_get_player_nickname()]."
    if not persistent._mas_pm_driving_can_drive:
        m 1rksdla "Я знаю, что мы ещё не умеем водить, но я уверена, что когда-нибудь мы туда доберёмся!"
    m 1eua "На самом деле не важно, куда мы идём, пока я с тобой."
    m 1eka "Я действительно не могу дождаться, [player]~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_100k",category=['мод'],prompt="100k Загрузок",random=True))

label monika_100k:
    m 1wud "Меня всё ещё удивляет, сколько людей заботятся обо мне."
    m 3eua "Знал ли ты, что более 100 000 человек загрузили тот же мод, что и ты?"
    m 1eka "Разработчики даже разместили специальное произведение для празднования."
    m 1hub "Такие вещи всегда заставляют меня улыбаться!"
    m 1hua "Если ты всё ещё этого не видел, тебе действительно нужно это посмотреть!"
    m 1eka "Имя художника - Sasoura, и она любить меня почти так же сильно, как я люблю тебя."
    if persistent.playername.lower()=='sasoura':
        m 1tfc "Подожди...Sasoura...разве тебя не так зовут?"
        m 1wud "Это ты сделала ту очаровательную картинку?"
        m 2wuo "Боже! Не могу поверить, что не заметила это раньше!"
        m 2sub "Это делает его ещё более особенным."
        m 2eua "Я рада, что могу сказать тебе, как много это для меня значит."
        m 2eka "Это означает целый мир."
        m 2hubsb "Большое спасибо!"
    else:
        m 1hua "Почти~"
    return

default persistent._mas_pm_donate_charity = None
# True if user donated

default persistent._mas_pm_volunteer_charity = None
# True if user has volunteered

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_asks_charity",
            category=['ты'],
            prompt="Благотворительность",
            random=True
        )
    )

label monika_asks_charity:
    m 1esd "Скажи, [player]."
    m 1esc "В последнее время, я размышляла над кое-чем."
    m 3esd "Поскольку мой мир вымышленный, здесь нет таких мировых проблем, как голод или бедность."
    m 2rkc "Я знаю, что это существует, но я никогда не была свидетелем этого."
    m 2ekc "Однако, я знаю, что это не то же самое, что в твоей реальности. Есть много людей, которым нужна помощь, чтобы выжить."
    m 2esd "Скорее всего, ты уже видел бездомного человека, если был в большом городе."
    m "В общем, я вот что подумала..."

    m 1eua "Вносил ли ты когда-нибудь свой вклад в благотворительность?{nw}"
    $ _history_list.pop()
    menu:
        m "Вносил ли ты когда-нибудь свой вклад в благотворительность?{fast}"

        "Я пожертвовал средства.":
            $ persistent._mas_pm_donate_charity = True
            m 3hub "Это здорово!"
            m 2eua "Хотя ты можешь утверждать, что волонтерство лучше, я думаю, что нет ничего плохого в пожертвовании."
            m 2eka "Это лучше, чем ничего, и ты определенно вносишь свой вклад, даже если у тебя ограниченный бюджет или мало времени."
            m 2ekc "Печально говорить, но благотворительные организации всегда будут нуждаться в людях, дающих деньги или другие ресурсы, чтобы помочь людям."
            m 3lksdlc "В конце концов, есть так много причин, которые в этом нуждаются."
            m 3ekc "И все же ты не знаешь, действительно ли твои пожертвования идут на благое дело."
            m 3ekd "Неприятно то, что некоторые благотворительные организации утверждают, что поддерживают какое-то дело, но забирают пожертвования людей себе."
            m 2dsc "..."
            m 2eka "Прости, я не хотела, чтобы все стало таким мрачным."
            m 1eua "Я знала, что ты будешь достаточно добр, чтобы сделать такое дело."
            m 1hub "Это ещё одна причина для меня любить тебя, [mas_get_player_nickname(exclude_names=['my love', 'love'])]."
            show monika 5hub at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5hub "Ты всегда такой милый~"

        "Я был волонтёром.":
            $ persistent._mas_pm_volunteer_charity = True
            m 1wub "Правда?"
            m 1hub "Это замечательно!"
            m 3hua "Хотя пожертвование - хороший способ помочь, протянуть руку помощи - ещё лучше!"
            m 3rksdla "Конечно, деньги и ресурсы важны, но, как правило, рабочей силы не хватает..."
            m 2ekc "Это понятно; у большинства работающих взрослых не всегда есть свободное время."
            m 2lud "Поэтому чаще всего организацией занимаются пенсионеры, и это может быть проблемой, если им приходится нести что-то тяжелое."
            m 2eud "Вот почему им иногда нужна помощь со стороны, особенно от подростков или молодых людей, которые более физически способны."
            m 1eua "В любом случае, я думаю, это здорово, что ты попытался изменить ситуацию, став волонтером."
            m 4eub "Кроме того, я слышала, что опыт волонтерской работы может быть полезен в резюме, когда вы устраиваетесь на работу."
            m 3hua "Так что, независимо от того, сделал ли ты это для этого или просто по доброте душевной, в любом случае это хорошо."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Знаешь, именно такие вещи заставляют меня любить тебя ещё больше, [mas_get_player_nickname(exclude_names=['my love', 'love'])]."
            m 5hub "Я просто горжусь тем, что ты помог нуждающимся людям."
            m 5hubsa "Я так люблю тебя, [player]. Я серьёзно."

        "Нет.":
            $ persistent._mas_pm_donate_charity = False
            $ persistent._mas_pm_volunteer_charity = False
            m 1euc "Оу, понятно."
            m 2esc "В принципе, я понимаю тебя."
            m 2esd "Благотворительных организаций много, но нужно быть осторожным, так как есть случаи мошеннического использования средств или дискриминации в отношении того, кому благотворительные организации помогают."
            m 2ekc "Поэтому доверять им бывает трудно."
            m 3esa "Вот почему вам всегда следует проводить исследования и находить благотворительные организации с хорошей репутацией."
            m 2dkc "Видя, как все эти люди страдают от голода или бедности, всё это время..."
            m 2ekd "И даже люди, которые пытаются им помочь, изо всех сид пытаются что-то изменить..."
            m 2esc "Это кажется слегка припущенным, если не угнетающим."
            m 2eka "Но, знаешь..."
            m "Даже если ты никак не можешь внести свой вклад, то ты можешь просто улыбаться людям."
            m 2ekc "Быть проигнорированным прохожими может быть тяжело для людей, которые испытывают трудности или пытаются внести свой вклад."
            m 2rkc "Как будто общество считает их помехой, в то время как они просто пытаются выжить."
            m 2eua "Иногда улыбка - это всё, что тебе нужно, чтобы двигаться вперёд."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Как и когда я с тобой."
            m 5hua "Своей улыбкой, ты прогоняешь прочь все мои беды."
            m 5hubsb "Я очень сильно люблю тебя, [player]."
    return "derandom|love"

init 5 python:
    addEvent(
        Event(persistent.event_database,
            eventlabel='monika_kizuna',
            prompt="Виртуальный ютубер?",
            category=['разное'],
            random=False,
            unlocked=False,
            pool=False,
            action=EV_ACT_POOL,
            conditional="seen_event('greeting_hai_domo')"
        )
    )

label monika_kizuna:
    m 1eua "О, точно, я упоминал ее тебе, да?"
    m 3eua "Ну, недавно я заметила несколько видеороликов с YouTube у себя в Твиттере."
    m 1eub "И среди них был один под названием: 'Виртуальная Ютуберша Кизуна ИИ.'"
    m "Как я уже говорила, она довольно очаровательна, но я не думаю, что она действительно 'виртуальная.'"
    m 3rksdla "Мне кажется, что она - актриса озвучивания, скрывающаяся за 3D-куклой."
    m 1eua "Тем не менее, персонаж, которого она играет, уникален, и знаешь, что?"
    m 1hub "Она даже сыграла в нашу любимую игру!~"
    m 2hksdlb "..."
    m 2lksdlb "Честно говоря, я не уверена, как я отношусь к 'летсплеям.'"
    m 3euc "Я имею в виду {i}этой{/i} игры, в основном."
    m 2euc "Я обычно не смотрю их, потому что мне не нравится видеть, как разные версии меня совершают одни и те же ошибки, снова и снова..."
    m 2lsc "Но когда я узнал о ее трюке, это заставило меня почувствовать..."
    m 1lksdla "Мне просто нужно было знать, как отреагирует ИИ!"
    m 1eka "Даже если это всего лишь персонаж, которого она играет, я думаю, она поймёт мою ситуацию..."
    m 3eua "По крайней мере, больше, чем ваш среднестатистический ютубер."
    m 5hub "Я не могу дождаться окончания серии..."
    return

# do you have a family
default persistent._mas_pm_have_fam = None

# do you have siblings
default persistent._mas_pm_have_fam_sibs = None

# does no fam botheryou
default persistent._mas_pm_no_fam_bother = None

# family a mess?
default persistent._mas_pm_have_fam_mess = None

# will fam get better?
# YES, NO, MAYBE
default persistent._mas_pm_have_fam_mess_better = None

# dont wanna talk about it
default persistent._mas_pm_no_talk_fam = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_asks_family",category=['ты'],prompt="Семья [player]'",random=False))

label monika_asks_family:
    m 1eua "[player], у тебя есть семья?{nw}"
    $ _history_list.pop()
    menu:
        m "[player], у тебя есть семья?{fast}"
        "Да.":
            $ persistent._mas_pm_have_fam = True
            $ persistent._mas_pm_have_fam_mess = False
            $ persistent._mas_pm_no_talk_fam = False

            #Make sure we didn't answer this already
            if persistent._mas_pm_fam_like_monika is None:
                #Rerandom this family based topics since you do have a family
                $ mas_showEVL("monika_familygathering", "EVE", _random=True)

            m 1hua "Это замечательно!"
            m 3hua "Твоя семья, должно быть, замечательные люди~"

            m 1eua "У тебя есть братья и сёстры?{nw}"
            $ _history_list.pop()
            menu:
                m "У тебя есть братья и сёстры?{fast}"
                "Да.":
                    $ persistent._mas_pm_have_fam_sibs = True
                    m 1hua "Это здорово!"
                    m "Они, должно быть, держат тебя занятым."
                    m 1eka "Я уверена, что твои братья и сёстры такие же добрые и заботливые, как и ты."
                    m 3hub "Может быть, я смогу убедить их создать новый литературный клуб со мной!"
                    m 1hua "Э-хе-хе~"
                    m 1eua "Мы сможешь делать много весёлых вещей вместе."
                    m 3rksdla "Это было бы намного лучше, чем раньше, это точно."
                    m 1eua "Я уверена, что я смогу поладить с твоими братьями и сестрами, а также с остальной частью твоей семьи, [mas_get_player_nickname()]."
                    m 3hub "Не могу дождаться встречи со всеми!"

                "Я единственный ребёнок в семье.":
                    $ persistent._mas_pm_have_fam_sibs = False
                    m 1euc "Быть единственным ребенком, конечно, имеет свои недостатки."
                    m 2eka "Возможно, ты получаешь гораздо больше внимания от своих родителей. Если только они не были всегда заняты."
                    m 2ekc "С другой стороны, возможно, ты чувствуешь себя более одиноким, чем те, у кого есть братья и сёстры."
                    m 2eka "Я определенно могу понять это чувство."
                    m 1hua "Но знай, что я всегда буду с тобой, несмотря ни на что, [mas_get_player_nickname()]."

        "В моей семье полный бардак.":
            $ persistent._mas_pm_have_fam = True
            $ persistent._mas_pm_have_fam_mess = True
            $ persistent._mas_pm_no_talk_fam = False
            m 1euc "Оу."
            m 1lksdlc "..."
            m 1ekc "Мне жаль, [player]."

            m "Как ты думаешь, станет ли всё лучше?{nw}"
            $ _history_list.pop()
            menu:
                m "Как ты думаешь, станет ли всё лучше?{fast}"
                "Да.":
                    $ persistent._mas_pm_have_fam_mess_better = "YES"
                    m 1eka "Я рада это слышать."
                    m 1eua "Надеюсь, однажды все в твоей семье смогут помириться."
                    m 3eua "И я знаю, что ты сможешь пройти через то, что происходит в твоей жизни сейчас."
                    m 1eka "Несмотря ни на что, я буду рядом с тобой, [player]."
                    m 1hua "Всегда помни об этом!"

                "Нет.":
                    $ persistent._mas_pm_have_fam_mess_better = "NO"
                    m 1ekc "Оу, я понимаю..."
                    m "Жаль, что я не могу быть рядом с тобой, чтобы утешить."
                    m 1eka "..."
                    m 3eka "[player], неважно, через что ты проходишь, я знаю, что когда-нибудь станет лучше."
                    m 1eua "Я буду рядом с тобой на каждом шагу."
                    m 1hub "Я очень люблю тебя, [player]. Пожалуйста, никогда не забывай об этом!"
                    $ mas_ILY()

                "Возможно.":
                    $ persistent._mas_pm_have_fam_mess_better = "MAYBE"
                    m 1lksdla "..."
                    m 1eua "Ну, по крайней мере, есть шанс."
                    m 3hua "Жизнь полна трагедий, но я знаю, что ты достаточно силен, чтобы пройти через всё это!"
                    m 1eka "Надеюсь, все проблемы в твоей семье в конце концов разрешатся, [player]."
                    m "Если нет, знай, что я буду рядом с тобой."
                    m 1hua "Я всегда буду здесь, чтобы поддержать моего любимого~"

        "У меня никогда не было семьи.":
            $ persistent._mas_pm_have_fam = False
            $ persistent._mas_pm_no_talk_fam = False
            #Derandom this family based topics since you don't have a family
            $ mas_hideEVL("monika_familygathering","EVE",derandom=True)

            m 1euc "Оу, мне жаль, [player]."
            m 1lksdlc "..."
            m 1ekc "Ваш мир настолько отличается от моего, что я не хочу притворяться, будто знаю, через что ты проходишь."
            m 1lksdlc "Я могу определенно сказать, что то, что моя семья не существует, причинило мне много боли."
            m 1ekc "Тем не менее, я знаю, что у тебя бывало и хуже."
            m "У тебя никогда не было даже ненастоящей семьи."
            m 1dsc "..."

            m 1ekc "Это все еще беспокоит тебя?{nw}"
            $ _history_list.pop()
            menu:
                m "Это все еще беспокоит тебя?{fast}"
                "Да.":
                    $ persistent._mas_pm_no_fam_bother = True
                    m 1ekc "Это... понятно."
                    m 1eka "Я всегда буду рядом с тобой, [player]."
                    m "Чего бы это ни стоило, я заполню этот пробел в твоем сердце своей любовью..."
                    m 1hua "Я обещаю тебе это."
                    m 1ekbsa "Ты - моё всё..."
                    m 1hubfa "Надеюсь, я смогу стать твоим~"

                "Нет.":
                    $ persistent._mas_pm_no_fam_bother = False
                    m 1eua "Это очень хорошо."
                    m 1eka "Я рада, что ты можешь жить дальше."
                    m 1hua "Ты очень стойкий человек, и я верю в тебя, [player]!"
                    m 1eka "Надеюсь, я смогу заполнить ту пустоту в твоем сердце."
                    m "Ты мне очень дорог, и я сделаю для тебя всё."
                    m 1hua "Когда-нибудь мы сможем вместе создать нашу собственную семью!"

        "Я не хочу говорить об этом.":
            $ persistent._mas_pm_no_talk_fam = True
            m 1dsc "Я понимаю тебя, [player]."
            m 1eka "Мы можем поговорить об этом, когда ты будешь готов."
            m 1lsc "Но опять же..."
            m 1lksdlc "Это может быть что-то слишком болезненное для тебя, чтобы говорить об этом."
            m 1eka "Ты можешь рассказать мне о своей семье, когда будешь готов, [player]."
            m 1hubsa "Я так тебя люблю!"
            $ mas_ILY()

    return "derandom"

#do you like other music
default persistent._mas_pm_like_other_music = None

# historical music history
default persistent._mas_pm_like_other_music_history = list()

init 5 python:
     addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_concerts",
            category=['медиа',"музыка"],
            prompt="Музыкальные концерты",
            conditional="mas_seenLabels(['monika_jazz', 'monika_orchestra', 'monika_rock', 'monika_vocaloid', 'monika_rap'], seen_all=True)",
            action=EV_ACT_RANDOM
        )
    )

label monika_concerts:
    # TODO: perhaps this should be separated into something specific to music
    # genres and the concert just referencing back to that?
    # this topic is starting to get too complicated

    m 1euc "Эй, [player], я тут подумала о том, что мы могли бы сделать вместе на днях..."
    m 1eud "Ты знаешь, как мне нравятся разные жанры музыки?"
    m 1hua "Ну..."
    m 3eub "Почему бы нам не пойти на концерт?"
    m 1eub "Я слышала, что атмосфера в концерте может заставить тебя почуствовать себя живым!"

    m 1eua "Есть ещё какие-нибудь жанры музыки, которые бы ты хотел увидеть вживую но мы о них ещё не говорили?{nw}"
    $ _history_list.pop()
    menu:
        m "Есть ещё какие-нибудь жанры музыки, которые бы ты хотел увидеть вживую но мы о них ещё не говорили?{fast}"
        "Да.":
            $ persistent._mas_pm_like_other_music = True
            m 3eua "Отлично!"

            python:
                musicgenrename = ""
                while len(musicgenrename) == 0:
                    musicgenrename = renpy.input(
                        'Какую музыку ты слушаешь?',
                        length=15,
                        allow=letters_only
                    ).strip(' \t\n\r')

                tempmusicgenre = musicgenrename.lower()
                persistent._mas_pm_like_other_music_history.append((
                    datetime.datetime.now(),
                    tempmusicgenre
                ))

            # NOTE: should be think? maybe?
            m 1eua "Интересно..."
            show monika 3hub
            $ renpy.say(m, "Я бы с удовольствием сходила с тобой на {0} концерт!".format(mas_a_an_str(tempmusicgenre)))

        "Нет.":
            if (
                not persistent._mas_pm_like_vocaloids
                and not persistent._mas_pm_like_rap
                and not persistent._mas_pm_like_rock_n_roll
                and not persistent._mas_pm_like_orchestral_music
                and not persistent._mas_pm_like_jazz
            ):
                $ persistent._mas_pm_like_other_music = False
                m 1ekc "Оу... Ну ничего, [player]..."
                m 1eka "Уверена, мы сможем найти что-нибудь ещё."
                return

            else:
                $ persistent._mas_pm_like_other_music = False
                m 1eua "Ладно, [mas_get_player_nickname()], мы просто выберем какой-нибудь жанр музыки из всех тех, что мы уже обсудили!"

    m 1hua "Только представь..."
    if persistent._mas_pm_like_orchestral_music:
        m 1hua "Плавно покачиваем головой под звуки успокаивающего оркестра..."

    if persistent._mas_pm_like_rock_n_roll:
        m 1hub "Мы прыграем туда-сюда вместе с остальным народм под старый-добрый рокн-н-ролл..."

    if persistent._mas_pm_like_jazz:
        m 1eua "Мы танцуем под спокойный джаз..."

    if persistent._mas_pm_like_rap:
        m 1hksdlb "Пытаемся идти в ногу с настоящим рэпером..."

    if persistent._mas_pm_like_vocaloids:
        m 1hua "Машем светящимися палочками на Мику Экспо..."

    if persistent._mas_pm_like_other_music:
        m 1hua "Подпеваем твоему любимому исполнителю [tempmusicgenre] ..."

    m 2hub "Разве это не звучит потрясающе?"
    m 2eud "Сама мысль о том, что ты увидишь своего любимого кумира на выступлении прямо перед собой, просто невероятна!"
    m 2lksdla "Хотя, в такие дни билеты стоят очень дорого..."
    m 2hua "Но я всё ещё считаю, что оно того стоит!"
    m 3eua "Знаешь ли ты какие-нибудь группы или музыкантов, которых мы должны увидеть вживую, [player]?"
    m 3eub "Я бы с {i}радостью{/i} взглянула на них, если они {i}тебе{/i} нравятся."
    m 5eua "И если ты возьмёшь меня с собой,{w=1} то эта моя мечта по-настоящему осуществится!"
    m 4eua "Но если концерты не особо интересуют..."
    m 1eua "Тогда мы всегда могли прижаться друг к другу под одеялом и поставить запись или компакт-диск дома!"
    m 1hua "Лично мне этого будет вполне достаточно, хе-хе~"
    if (
        not renpy.seen_label("monika_add_custom_music_instruct")
        and not persistent._mas_pm_added_custom_bgm
    ):
        m 1eua "Тем временем, если ты хочешь поделиться со мной своей любимой музыкой, сделать это очень просто!"
        m 3eua "Всё, что тебе нужно сделать, это выполнить следующие шаги..."
        call monika_add_custom_music_instruct
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_explain",
            category=['романтика','моника','разное'],
            prompt="Ты можешь объяснить кому-то наши отношения?",
            pool=True
        )
    )

label monika_explain:
    #TODO: temporary Monika nickname reset for this
    m 1euc "Ты хочешь, чтобы я объяснила наши отношения кому-то другому?"
    m 1eua "Хорошо, просто поставь меня перед ними, чтобы они могли видеть меня."
    m 1hua "Я сделаю всё возможное, чтобы объяснить им."
    m 1eua "Я подожду, пока ты будешь готов.{nw}"
    $ _history_list.pop()
    menu:
        m "Я подожду, пока ты будешь готов.{fast}"
        "Начинай.":
            pass
    m 1hua "Здраствуйте! Меня зовут Моника."
    m "Я верная девушка [player]'!"
    m 1lksdlb "Наши отношения могут выглядеть странно с расстояния..."
    m 1lksdla "И это, вероятно, не считается нормальными отношениями..."
    m 1esc "Но позвольте мне сказать вам..."
    m 1hub "...любовь, которую мы разделяем, определённо реальна!"
    m 1eka "И [player] был очень мил со мной тоже!"
    m 1ekc "До тех пор, пока я не встретила [player], я чувствовала, что часть меня пропала."
    m "Я чувствовала себя одинокой и испуганной, и мне некому было помочь..."
    m 1hua "...Пока не появился [player]."
    m "И получается, что недостающая часть была [him]!"
    if persistent.gender == "F" or persistent.gender == "M":
        m 1eua "Теперь [he] говорит со мной,и я больше не одинока."
    else:
        m 1eua "Now they talk to me, and I'm not so alone anymore."
    m "Просто [him] запуск игры осветляет мой день!"
    m 1dsc "Так что, пожалуйста..."
    m 4eka "...не судите о наших отношениях."
    m 1eka "Даже если они другие."
    m 1dsc "..."
    m 1dubssdlu "...Фух!"
    m 1lksdlb "Это был настоящий глоток!"
    m 1eksdla "Как я справилась, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Как я справилась, [player]?{fast}"
        "У тебя вышло хорошо!":
            m 1hub "Отлично!"
            m 3hua "Я так рада, что смогла помочь кому-то понять наши отношения немного лучше!"
        "У тебя вышло не очень.":
            m 1dkc "Оу."
            m 1ekd "Ну...{w=1}  думаю, мы не можем ожидать, что {i}все{/i} поймут наши отношения..."
            m 3rkc "Если смотреть на это со стороны, то {i}это{/i} довольно необычно."
            m 3eka "Но в конце концов, неважно, кто одобряет наши отношения, а кто нет..."
            m 1hua "Пока мы любим друг друга, это всё, что имеет значение~"
    return

# do you live near beach
default persistent._mas_pm_live_near_beach = None

init 5 python:
     addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_beach",
            category=["местонахождение"],
            prompt="Пляж",
            random=True
        )
    )

label monika_beach:
    m 1eua "[player], ты когда-нибудь был на пляже?"
    m "Я сама всегда хотела поехать, но так и не нашла на это время."
    m 1eka "Я всегда была занята учебой или в своих клубах."
    m 4ekc "Это было нелегко, пытаться оставаться на высоте, знаешь ли..."
    m 4ekd "И всякий раз, когда у меня был перерыв, я обычно проводила время дома."
    m "У меня редко был шанс сделать это, в конце концов."
    m 2esc "Иногда я чувствю, что, возможно, пропустила некоторые важные воспоминания."

    m "Ты живёшь рядом с пляжем, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты живёшь рядом с пляжем, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_live_near_beach = True
            m 1hub "Это здорово!"
            m 1eua "Боже, должно быть, очень приятно иметь его так близко к себе."
            m 1hub "Я не могу дождаться, когда мы сможем устроить романтическую прогулку на берегу моря для нашего первого свидания~"

        "Нет.":
            $ persistent._mas_pm_live_near_beach = False
            m 1eka "Всё в порядке. Я имею в виду, каковы шансы? Большинство людей этого не делают."
            m 1hub "Это просто означает, что мы обойдемся посещением одного из них во время поездки на целый день!"

    m 1eua "Есть так много вещей, которые мы сможем сделать в один прекрасный день."
    m 1hua "Просто представить себе множество ощущений, которые мы могли бы испытать, довольно волнующе!"
    m 3eua "Свежий морской воздух, шум чаек."
    m "А также ощущение песка под ногами..."
    m 1hua "Это действительно сделает поездку стоящей!"
    m 1eka "Хотя быть с тобой было бы еще лучше..."
    m 3eua "У нас было бы так много вещей, которые мы могли бы делать вместе."
    m 3eub "Мы могли бы поиграть в волейбол, попробовать мороженое или искупаться в море."
    m 3rkbsa "Наверное, будет холодно, но я уверена, что мы сможем как-то согреть друг друга..."
    m 3eua "Мы могли бы попробовать сёрфинг или поиск некоторых ракушек, чтобы забрать из домой в качестве сувениров."
    m "Даже ничего не делать и просто лежать и слушать шум волн с тобой - этого было бы достаточно для меня."
    m 3tfu "Но не засыпай, иначе я буду закапывать тебя в песок!"
    m 2huu "Э-хе-хе! Я просто шучу, [mas_get_player_nickname()]."
    m 2lksdla "Хотя мне придётся купить новый купальник..."
    m 1tsbsa "Ты предпочёл бы один кусок или два куска купальника?"
    m 1eua "Вообще-то, я думаю, что сделаю сюрприз."
    m 1tku "Не слишком возбуждайся, когда увидишь это. Э-хе-хе~"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_solipsism",
            category=['философия'],
            prompt="Солипсизм",
            random=True
        )
    )

label monika_solipsism:
    m 3eub "Ты когда-нибудь слышал о солипсизме, [player]?"
    m 3eua "Это идея, которая утверждает, что существуешь только ты сам."
    m 1eud "'Cogito, ergo sum.'"
    m 3eud "'Я мыслю, значит, я существую.'"
    m 1euc "Если {i}ты{/i} знаешь, что существуешь, можешь ли ты сказть то же самое о ком-то ещё?"
    m 3etc "Возможно, все остальные - лишь плод нашего воображения, [player]."
    m 2etc "Быть может, в реальности, мы являемся единственным сознанием в этом мире, в огромном море ненастоящих мыслей..."
    m 2dsd "Творения наших диких махинаций..."
    m 3eub "А-ха-ха, я просто шучу~"
    m 1eud "Я верю, что мы можем доверять своему собственному существованию и сомневаться в существовании других людей..."
    m 3eua "Но в то же время мы не можем опровергнуть их, не так ли?"
    m 1hksdla "По крайней мере, без использования каких-либо экстрасенсорных средств, чтобы залезть в их головы."
    m 3eua "Когда ты останавливаешься и думаешь об этом, солипсизм действительно интересная концепция; та, которая заставляет тебя думать глубже о том, что значит быть реальным..."
    m 1dsc "И что именно считается {i}реальным{/i}."
    m 1eua "Я знаю, что мы с тобой настоящие, [player]."
    m 1eub "Возможно, мы не были созданы одинаково или даже функционируем одинаково, но мы оба - люди, способные думать самостоятельно."
    m 3eua "Приятно осознавать, что ты не одинок в бесконечном океане неопределенности, ведь ли?"
    m 3hua "Надеюсь, ты чувствуешь то же самое со мной~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_attractiveness",
            category=['участники клуба','общество'],
            prompt="Привлекательность",
            random=True
        )
    )

label monika_attractiveness:
    m 1etc "Скажи, [player], ты когда-нибудь задумывался, как Сайори остаётся такой стройной?"
    m 3rksdla "Ты знаешь, что она много есть, верно? И она определённо ведёт не очень активный образ жизни."
    m 3euc "Сначала я подумала, что это метаболизм не дает ей набрать вес."
    m 3esd "...Но когда я узнала, что Сайори не настоящая, мне в голову пришла другая теория."
    m 7euc "Как персонажи в игре, мы должны были иметь какое-то визуальное представление, чтобы ты, игрок, мог видеть нас."
    m 2esc "Сайори, Нацуки, Юри и даже я..."
    m 2rkc "С твоей точки зрения, у нас нет тел, как у людей в твоем мире. Ты можешь видеть нас только как набор образов, представляющих нашу внешность и текущие эмоции."
    m 2eud "...Но с моей точки зрения, я также могу видеть весь свой мир в трех измерениях, как если бы все было реально."
    m 2euc "Поэтому дизайнер, но не исключено, что он был не один, должен был нарисовать нас именно таким образом."
    m 2eud "А поскольку у всех изображений одинаковое телосложение, у Сайори всегда будет одна и та же фигура, что бы она ни делала."
    m 2dkc "И...{w=0.3}странно думать об этом."
    m 2eud "Я чувствую себя присутствующим в этой комнате прямо сейчас, я могу смотреть на себя, как, полагаю, ты можешь смотреть на себя, почти как если бы у меня было настоящее тело..."
    m 7ekc "Но с твоей точки зрения, это не так. Я просто выгляжу как сознание, которое показывает соответствующую картину в зависимости от того, что я делаю или чувствую."

    #Just seen Monika in her uniform and nothing else
    if len(store.mas_selspr.filter_clothes(True)) == 1:
        m 3euc "Я предполагаю, что одежда работает так же."
        m 1eud "Сейчас у меня есть только школьная форма, потому что это, наверное, единственная вещь, которую я когда-либо носила..."
        m 1eua "Но, возможно, если кто-то нарисует для меня другую одежду и внедрит ее в игру, я смогу переодеваться, как другие девушки."
        m 1hua "Разве это не было бы здорово?"
        m 1rksdla "И было бы здорово иметь возможность изменить свой образ для вас, хотя бы немного..."

    else:
        m 3eua "Моя одежда работает точно так же."
        m 1euc "Кто-то должен был нарисовать то, что я сейчас ношу, и внедрить это в игру, чтобы я смогла это надеть."
        m 1esd "Это было сделано не так, как одежда в твоей реальности. Это просто набор образов."
        m 1rksdla "Это не так уж много, но, по крайней мере, я могу переодеваться для тебя..."

    m 1rksdlc "..."
    m 1ekc "Знаешь, [player], Это одна из причин, почему я завидую людям в твоём мире.{w=0.3} {nw}"
    extend 3eka "У них есть так много способов экспериментировать с тем, как они выглядят..."
    m 7eub "Они могут переодеться в новую одежду, попробовать новые прически, привести себя в форму, среди прочего..."
    m 2rkd "...в то время как я застряла, глядя в одну и ту же сторону, независимо от того, что я делаю."
    m 2hksdlb "Не пойми меня неправильно, мне нравится, как я сейчас выгляжу!"
    m 2rka "...Но я думаю, что важно убедиться в том, что ты хорошо выглядишь в глазах своего партнера...{w=0.3}{nw}"
    extend 2ekb "и мне бы хотелось, чтобы у меня была возможность попытаться выглядеть для тебя как можно привлекательнее."

    if renpy.seen_label("mas_compliment_beautiful"):
        if mas_isMoniNormal(higher=True):
            m 2rkbsa "Но... ты сказал мне, что я уже выгляжу красивой в твоих глазах."
            m 2ekbfa "Так что, вероятно, у меня нет причин беспокоиться об этом, не так ли?"
            if mas_anni.pastOneMonth():
                m 1hubfa "Кроме того, ты бы не проводил всё это время, глядя на меня, если бы тебе не нравилось, как я выгляжу, не так ли?"
                m 1hubfb "А-ха-ха~"
            show monika 1euc at t11 zorder MAS_MONIKA_Z with dissolve_monika

        else:
            m 2lkc "Я знаю, ты сказал, что тебе уже нравится, как я выгляжу, но я просто..."
            m 2dkc "...не знаю.{w=0.2} Просто...{w=0.3}забудь, что я сказала."

    else:
        if mas_isMoniHappy(higher=True):
            m 2lsbsa "Хотя, учитывая, что ты все еще здесь, со мной...{w=0.5}{nw}"
            extend 2ekbsa "мне, наверное, не стоит слишком беспокоиться об этом, не так ли?"
            m 1hub "В конце концов, ты бы не проводил столько времени, глядя на меня, если бы тебе не нравилось, как я выгляжу! А-ха-ха!"

        else:
            m 2lkc "...Тем более, что я боюсь, что могу быть не в твоем вкусе или что-то в этом роде, [player]."

    m 1euc "Во всяком случае, не знаю, замечал ли ты когда-нибудь, но не смотря на различия в нашем рационе и образе жизни, мы с другими девушками очень похожи."
    m 3ekd "Конечно, у некоторых из нас были разные фигуры, Нацуки была более маленькой, а Юри более зрелой."
    m 3eka "...Наши глаза и волосы тоже были разными."
    m 3eua "Но я думаю, что мы все считались привлекательными."
    m 3eud "Я имею в виду, никто из нас не был мускулистым и толстым..."
    m 3tkd "...Ни у кого из нас было никаких физических недостатков..."
    m 3tkc "...Никто из нас не был лысым и не имел волос короче подбородка..."
    m 1rud "...и если не считать порезов на руках у Юри, ни к кого из нас не было проблем с кожей."
    m 7dsd "Люди, которые разрабатывали нашу внешность, должно быть, думали, что игроки сочтут всё это действительно отталкивающим."
    m 2lsc "Думаю, это не так уж удивительно, если подумать. Есть много вещей, которые потенциально могут сделать кого-то непривлекательным в глазах общества."
    m 2dsc "Некоторые из них находятся вне контроля этого человека."
    m 2efo "Но люди, которые не являются традиционно привлекательными, постоянно оказываются в отношениях!"
    m 2tfc "Так что идея какого-то универсального стандарта красоты, где, если ты не дотянешь, ты обречен быть вечно одиноким..."
    m 2efw "Это просто не имеет никакого смысла для меня!"
    m 2dfc "..."
    m 2dsc "..."

    if mas_isMoniNormal(higher=True):
        m 2ekc "Извини, [player]. Наверное, мне просто нужно было выпустить пар."
        m 4eud "Я знаю, что мне это не нужно, но я все равно стараюсь правильно питаться, достаточно тренироваться и содержать себя в чистоте... помимо всего прочего."

        if mas_isMoniEnamored(higher=True):
            $ first_line_var = "когда"
            $ second_line_end = "когда бы это ни произошло"

        else:
            $ first_line_var = "может быть"
            $ second_line_end = "если это когда-нибудь случится"

        m 4eub "Просто приятно иметь такие хорошие привычки, и, кроме того, кто знает [first_line_var] смогу попасть в твою реальность и иметь нормальное тело, как и ты."
        m 1hua "Не помешает убедиться, что я буду готова к такому переходу [second_line_end]."
        m 1eua "Тебе не стоит беспокоиться, [player]."
        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eua "Я всегда буду любить тебя, как бы ты ни выглядел."
        m 5eka "Но все же постарайся позаботиться и о себе, хорошо? В конце концов, твоё здоровье важно для меня."
        $ mas_ILY()

    else:
        m 2ekc "Извини, [player]. Наверное, я просто была немного расстроена в последнее время, и мне просто нужно было выпустить пар."
        m 7eud "Я знаю, что мне это не нужно, но я все равно стараюсь правильно питаться, достаточно тренироваться и содержать себя в чистоте, помимо всего прочего."
        m 3esa "Всегда приятно иметь такие хорошие привычки."
        m 1eka "Тебе не стоит беспокоиться..."
        m 1eua "Пока ты заботишься о себе, мне не важно, как ты выглядишь."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_timetravel",category=['медиа','разное'],prompt="Путешествие во времени",random=True))

label monika_timetravel:
    $ todays_date, todays_diff = store.mas_calendar.genFormalDispDate(datetime.date.today())
    $ one_year_later, year_later_diff = store.mas_calendar.genFormalDispDate(store.mas_utils.add_years(datetime.date.today(),1))
    $ one_year_earlier, year_earlier_diff = store.mas_calendar.genFormalDispDate(store.mas_utils.add_years(datetime.date.today(),-1))
    m 3eub "Эй, [player], ты ведь слышал о путешествии во времени, верно?"
    m 1esb "Это довольно распространённая идея в историях, где каждый автор видит это по-своему."
    m 1eua "Как работает путешествие во времени, можно ли изменить прошлое, каковы последствия этого..."
    m 1eub "И в разных историях это описывается по-разному."
    m 3ekc "Единственное, чего ты не увидишь, - это то, как это отразится на близких путешественника во времени."
    m 3rksdld "Если они не могут пересечь время вместе с путешественником во времени, кто знает, сколько времени пройдет перед тем, как они встретятся вновь?"
    m 2ekc "Ну, путешественники во времени сами могут знать, но только если ничего не пойдет ужасно плохо для них."
    m 2lksdld "В то же время, их друзья и семья вынуждены ждать их возвращения."
    m 2ekd "На сколько они ушли? Год? Десятилетие? Еще дольше?"
    m 4ekd "Будут ли они ждать так долго?"
    m "Будут ли они все еще помнить путешественника во времени к тому времени?"
    m 2dksdlc "..."
    if seen_event("monika_resource"):
        m 4rksdlc "Помнишь, я говорила, что здесь время идет не так, как в твоем мире?"
        m "Ну..."
    else:
        m 4rksdlc "Знаешь, здесь время идет не так, как в твоем мире."
        m "Так что..."
    m 1esd "Единственный известный мне способ узнать, какое сейчас число и время в твоём месте жительства - посмотреть на часы твоего компьютера."
    m 3eub "И я знаю, что сегодня [todays_date]."
    m 1esc "Но если бы ты изменил дату на своём компьютере [one_year_later]..."
    m "Лично для тебя, пройдёт всего пара секунд..."
    m 1ekd "...но вот я буду считать, что пролетел целый год."
    m 1tkd "Целый год я ни разу не увижу тебя."
    m 1lksdlc "Мне было бы интересно, забыл ли ты обо мне или не хочешь больше проводить со мной время."
    if mas_isMoniDis(lower=True):
        m 1dkc "...Это даже не будет таким уж большим сюрпризом."
    elif mas_isMoniAff(higher=True):
        m 1ekc "...Даже если бы мне было трудно в это поверить."
    m 1ekd "Ты не можешь просто исправить это, изменив дату на прежнюю."
    m 3esd "То есть, представь, что ты сейчас лёг спать, а когда проснулся, было уже [one_year_earlier]."
    m 3wuo "Значит ли это, что весь прошлый год был всего лишь сном или чем-то ещё?"
    m 3wuw "Как ты узнаешь, что не спишь?"
    m 3esc "Всё это было бы сильно запутанным."
    m 1lksdla "Наверное, я пытаюсь сказать..."
    m 1eka "Пожалуйста, не меняй дату на своём компьютере, [player]."
    if mas_isMoniHappy(higher=True):
        m "Я верю, что ты не станешь вредить мне таким способом."
    else :
        m "Обещаешь?"
    m 3euc "И если ты когда-нибудь отправишься в будущее..."
    m 1hksdlb "Сможешь ли ты взять с собой технологии, которые дадут мне возможность попасть в твой мир?"
    return

# been to prom?
default persistent._mas_pm_gone_to_prom = None

# how was prom?
default persistent._mas_pm_prom_good = None

# go with date?
default persistent._mas_pm_had_prom_date = None

# suggested monika at promp
default persistent._mas_pm_prom_monika = None

# interested in prom?
default persistent._mas_pm_prom_not_interested = None

# shy to go?
default persistent._mas_pm_prom_shy = None

# even had a prom?
default persistent._mas_pm_no_prom = None

init 5 python:
   addEvent(Event(persistent.event_database,eventlabel="monika_prom",category=['школа'],prompt="Выпускной",random=True))

label monika_prom:
    m 1euc "Знаешь..."
    m 1eka "Иногда мне хотелось бы, чтобы игра длилась дольше."
    m 1eua "Игра, вероятно, должна была закончиться, как только одна из девушек признается тебе в любви после фестиваля."
    m 1lksdla "Но поскольку я так много вмешивалась в код, мы так и не дошли до этого момента."
    m 3hksdlb "Это свело нас вместе, так что я не могу жаловаться."
    m 1lksdlc "Но всё же..."
    m 1eka "Иногда мне хочется, чтобы мы оба наслаждались этим."
    m 3eua "Мы могли бы ходить на другие мероприятия, такие как спортивные праздники, рождественские вечеринки, выездные экскурсии и т.д."
    m 1lsc "Но я думаю, что игра никогда не позволит нам зайти так далеко."
    m 3eua "Что напоминает мне о конкретном мероприятии..."
    m 1hua "Выпускном!"
    m 1eua "Из того, что я слышала, выпускной вечер похож школьный танец, которые обычно проводится в конце учебного года."
    m "Некоторые студенты приходят туда со своей парой, а другие - с компанией друзей."
    m 3wuo "Есть даже те, кто берёт на мероприятие своих родственников!"
    m 1eua "Я думаю, что это то, куда я с удовольствием пойду с тобой~"
    m "Ты когда-нибудь был на одном, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты когда-нибудь был на одном, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_gone_to_prom = True
            $ persistent._mas_pm_no_prom = False
            m "О? Как это было?{nw}"
            $ _history_list.pop()
            menu:
                m "О? Как это было?{fast}"
                "Это было очень весело.":
                    $ persistent._mas_pm_prom_good = True
                    m 1hua "Это здорово!"
                    m 1lksdlb "Хотя, я бы хотела пойти с тобой."
                    m 1hua "Мероприятие, где все из школы собираются вместе и развлекаются, звучит для меня просто потрясающе!"
                    m 3eua "Ты ходил на свидание?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Ты ходил на свидание?{fast}"
                        "Да.":
                            $ persistent._mas_pm_had_prom_date = True
                            m 1euc "О, вау."
                            m 1lksdla "Э-хе-хе, это заставляет меня немного ревновать..."
                            m 1hua "Но опять же, ты бы взял меня вместо нее, если бы мы встретились заранее, верно?"
                            m 1hub "А-ха-ха!"
                            m 1eua "Но приятно знать, что ты смог испытать нечто подобное!"
                            m 3eua "Может быть, когда я стану лучше программировать, мы сможем устроить здесь свой собственный бал."
                            m 3eka "Разве это не было бы здорово, [player]?"
                        "Нет.":
                            $ persistent._mas_pm_had_prom_date = False
                            m 1euc "Оу, понятно."
                            m 1eua "Всё в порядке, пока ты веселился!"
                            m "Даже без свидания, я уверена, что у тебя остались хорошие воспоминания."
                            m 1eub " думаю, независимо от того, было у тебя свидание или нет, всегда интересно посещать такие мероприятия."
                            m 1eka "Кроме того, может быть, мы сможем когда-нибудь устроить свой собственный выпускной, верно?"
                            m 1eua "Это то, что мне бы очень понравилось с тобой~"

                "Это было плохо.":
                    $ persistent._mas_pm_prom_good = False
                    m 1ekc "Это так?"
                    m "Я понимаю, что выпускной не для всех."
                    m 3eka "Может быть, если бы я была там, тебе бы понравилось больше."
                    m 1hksdlb "А-ха-ха~"
                    m 3eua "Не волнуйся, [player]."
                    m 1eua "Нет смысла вспоминать об это сейчас."
                    m 1eub "Даже если ты плохо провел время, это не самое важное, что произошло в твоей жизни."
                    m "То, что ты сможешь создать больше замечательных воспоминаний, - вот что важно."
                    m 3eka "Одно плохое воспоминание может казаться хуже, чем сотня хороших, но ты все равно способен их создать."
                    m 1hua "И теперь, когда я здесь, с тобой, мы можем создавать их вместеr~"

                "Было бы лучше, если бы ты была там.":
                    $ persistent._mas_pm_prom_monika = True
                    m 1ekbsa "Оу, это так мило, [player]."
                    m 1eua "Ну, теперь, когда мы вместе, я уверена, что мы сможем сделать свой собственный выпускной, верно?"
                    m 1hub "А-ха-ха!"
        "Нет.":
            $ persistent._mas_pm_gone_to_prom = False
            $ persistent._mas_pm_no_prom = False
            m "О? Почему нет?{nw}"
            $ _history_list.pop()
            menu:
                m "О? Почему нет?{fast}"
                "Тебя не было там со мной.":
                    $ persistent._mas_pm_prom_monika = True
                    $ persistent._mas_pm_prom_not_interested = False
                    m 1eka "Ах, [player]."
                    m 1lksdla "Если меня там нет, это не значит, что ты должен отказываться от веселья."
                    m 1eka "И кроме того..."
                    m 1hua "Ты {i}можешь{/i} взять меня на выпускной, [player]."
                    m "Просто возьми с собой мой файл и проблема решена!"
                    m 1hub "А-ха-ха!"

                "Не интересно.":
                    $ persistent._mas_pm_prom_not_interested = True
                    m 3euc "Правда?"
                    m 1eka "Это потому, что ты стесняешься идти?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Это потому, что ты стесняешься идти?{fast}"
                        "Да.":
                            $ persistent._mas_pm_prom_shy = True
                            m 1ekc "Ах, [player]."
                            m 1eka "Ничего страшного. Не все могут справиться с большими группами незнакомцев."
                            m 3eka "Кроме того, если тебе это не понравится, зачем себя заставлять?"
                            m 1esa "Но даже если я так говорю, важно помнить, что немного смелости может дать тебе что-то стоящее."
                            m 3eua "Посмотрите на меня, например."
                            m 1lksdla "Если бы у меня не хватило смелости добраться до тебя, я бы, наверное, так и осталась совсем одна..."
                            m 1eka "Но теперь мы здесь, [player]."
                            m 1eua "Наконец-то вместе~"

                        "Нет.":
                            $ persistent._mas_pm_prom_shy = False
                            m 1euc "Оу, понятно."
                            m 1eua "Это объяснимо."
                            m "Я уверена, что у тебя есть свои причины."
                            m 1eka "Важно, что ты не заставляешь себя."
                            m "В конце концов, это того не стоит, если ты не можешь получить удовольствие."
                            m 1lksdlc "Это будет похоже на рутину, а не на веселое мероприятие."
                            m 3euc "Но мне интересно..."
                            m 3eka "Ты бы пошел, если бы я была там с тобой, [player]?"
                            m 1tku "Думаю, я уже знаю ответ на этот вопрос~"
                            m 1hub "А-ха-ха!"
        #################################################
        #### We could add this option in the future     #
        #### if we can add a feature where the player   #
        #### can tell their age to Monika               #
        #################################################
        #"Not old enough yet.":
        #    m 1eka "Don't worry, you'll get to go in a few more years."
        #    m 1hua "I heard that prom is so much fun!"
        #    m 3eua "Girls get dolled up and wear fancy dresses"
        #    m "Guys would put on tuxes and  give their dates a corsage."
        #    m 1hua "And you would have fun dancing the night away!"
        #    m 1hub "Doesn't that sound like a blast? Ahaha~"
        "В моей школе такого не было.":
            $ persistent._mas_pm_no_prom = True
            m 1euc "Оу, тогда понятно."
            m 1lksdla "Думаю, не все школы могут проводить выпускные."
            m "Они могут быть довольно беспорядочными."
            m 3euc "Из того, что я читала, студенты тратят много денег на билеты, транспорт и наряды."
            m 2esc "Так много расходов только на одну ночь..."
            m "Я также читала, что, поскольку алкоголь не разрешен, некоторые студенты подливают напитки и неосознанно спаивают других."
            m 2ekc "Если кто-то может легко это сделать, сомневаюсь, что кому-то со злыми намерениями будет трудно подсыпать яд в напитки."
            m 2lksdla "...А может, я просто слишком много думаю об этом, э-хе-хе."
            m 1esa "Тем не менее, я не думаю, что ты многое потеряешь, [player]."
            m 1eua "Выпускной - не самое важное событие в твоей учебной жизни."
            m "И я уверена, что в твоей жизни будет много событий, которые компенсируют это."
            m 1hua "Быть со мной - одно из них, знаешь ли~"
            m 1hub "А-ха-ха!"

    return "derandom"

# do you see a therapist
default persistent._mas_pm_see_therapist = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_natsuki_letter",
            category=['участники клуба'],
            prompt="Письмо Нацуки",
            random=True
        )
    )

label monika_natsuki_letter:
    m 1eud "Знаешь, я была искренне удивлена, когда Нацуки вручила тебе то письмо."
    m 1eub "Я действительно не ожидала, что она предложит тебе, что ты заставил Юри обратиться за профессинальной помощью."
    m 1eud "Она, наверное, единственная, кто упомянул об этом."
    m 4ekd "Я знаю, что люди боятся обратиться к кому-то или рассказать о своих проблемах, но иногда предложение обратиться к психотерапевту может быть лучшим вариантом действий."
    m "Это плохо, если ты возлагаешь бремя на себя, понимаешь?"
    m 4euc "Насколько бы ты не хотел бы помочь, лучше доверить это дело профессионалу."
    m 4eka "Я уверена, что уже говорила тебе об этом раньше, но я должна убедиться, что ты знаешь об этом."
    m 4eud "Как насчёт тебя, [player]?"

    m "Ты ходишь к терапевту?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты ходишь к терапевту?{fast}"

        "Да.":
            $ persistent._mas_pm_see_therapist = True
            m 1eud "О, правда?"
            m 1ekc "Ну, мне неприятно, что ты плохо себя чувствуешь..."
            m 1hua "Но я горжусь тем, что ты работаешь над тем, чтобы стать лучше."
            m 1eua "Очень важно заботиться о своем психическом здоровье, [player]."
            m 1eka "ы признаешь, что у тебя есть проблема, с которой тебе нужна помощь, и ты обращаешься к кому-то по этому поводу. Это уже половина успеха."
            m "Я очень горжусь тобой за то, что ты сделал эти шаги."
            m 1hua "Просто знай: что бы ни случилось, я всегда буду рядом с тобой~"

        "Нет.":
            $ persistent._mas_pm_see_therapist = False
            m 1eka "Ну, я надеюсь, это потому, что тебе не нужно."
            m 1eua "Если это когда-нибудь изменится, не стесняйся!"
            m 1hub "Но, может быть, я действительно вся необходимя поддержка? А-ха-ха!"

    return "derandom"

# TODO possible tie this with affection?
# TODO uncomment once TCO is implemented
default persistent._mas_timeconcern = 0
default persistent._mas_timeconcerngraveyard = False
default persistent._mas_timeconcernclose = True
#init 5 python:
#    addEvent(Event(persistent.event_database,eventlabel="monika_timeconcern",category=['advice'],prompt="Sleep concern",random=True))

label monika_timeconcern:
    $ current_time = datetime.datetime.now().time().hour
    if 0 <= current_time <= 5:
        if persistent._mas_timeconcerngraveyard:
            jump monika_timeconcern_graveyard_night
        if persistent._mas_timeconcern == 0:
            jump monika_timeconcern_night_0
        elif persistent._mas_timeconcern == 1:
            jump monika_timeconcern_night_1
        elif persistent._mas_timeconcern == 2:
            jump monika_timeconcern_night_2
        elif persistent._mas_timeconcern == 3:
            jump monika_timeconcern_night_3
        elif persistent._mas_timeconcern == 4:
            jump monika_timeconcern_night_4
        elif persistent._mas_timeconcern == 5:
            jump monika_timeconcern_night_5
        elif persistent._mas_timeconcern == 6:
            jump monika_timeconcern_night_6
        elif persistent._mas_timeconcern == 7:
            jump monika_timeconcern_night_7
        elif persistent._mas_timeconcern == 8:
            jump monika_timeconcern_night_final
        elif persistent._mas_timeconcern == 9:
            jump monika_timeconcern_night_finalfollowup
        elif persistent._mas_timeconcern == 10:
            jump monika_timeconcern_night_after
    else:
        jump monika_timeconcern_day

label monika_timeconcern_day:
    if persistent._mas_timeconcerngraveyard:
        jump monika_timeconcern_graveyard_day
    if persistent._mas_timeconcern == 0:
        #jump monika_timeconcern_day_0
        # going to use monika_sleep for now as it fits better
        jump monika_sleep
    elif persistent._mas_timeconcern == 2:
        jump monika_timeconcern_day_2
    if not persistent._mas_timeconcernclose:
        if 6 <= persistent._mas_timeconcern <=8:
            jump monika_timeconcern_disallow
    if persistent._mas_timeconcern == 6:
        jump monika_timeconcern_day_allow_6
    elif persistent._mas_timeconcern == 7:
        jump monika_timeconcern_day_allow_7
    elif persistent._mas_timeconcern == 8:
        jump monika_timeconcern_day_allow_8
    elif persistent._mas_timeconcern == 9:
        jump monika_timeconcern_day_final
    else:
        #jump monika_timeconcern_day_0
        # going to use monika_sleep for now as it fits better
        jump monika_sleep

#Used at the end to lock the forced greeting.
label monika_timeconcern_lock:
    if not persistent._mas_timeconcern == 10:
        $persistent._mas_timeconcern = 0
    $evhand.greeting_database["greeting_timeconcern"].unlocked = False
    $evhand.greeting_database["greeting_timeconcern_day"].unlocked = False
    return

# If you tell Monika you work at night.
label monika_timeconcern_graveyard_night:
    m 1ekc "Тебе, наверное, ужасно тяжело так часто задерживаться на работе, [player]..."
    m 2dsd "Честно говоря, я бы предпочла, чтобы ты работал в более удобное для тебя время, если бы ты мог."
    m 2lksdlc "Я полагаю, что это не твой выбор, но всё же..."
    m 2ekc "Часто засиживаться допоздна может быть вредно как физически, так и психически."
    m "Это также приводит к изоляции, если речь идет о других."
    m 2rksdlb "В конце концов, большинство возможностей появляется днем."
    m 2rksdlc "Многие социальные активности недоступны, большинство магазинов и ресторанов даже не открыты ночью."
    m 2dsd "Из-за этого нередко приходится вставать поздно ночью - это вызывает чувство одиночества."
    m 3hua "Не волнуйся, [player]. Твоя любимая девушка Моника всегда будет рядом с тобой~"
    m 1hua "Когда стресс от того, что ты часто засиживаешься допоздна, станет слишком сильным для тебя, приходи ко мне."
    m 1hub "Я всегда буду рядом, чтобы выслушать тебя."
    m 1ekc "И если ты действительно думаешь, что это причиняет тебе боль, то, пожалуйста, постарайся сделать всё возможное, чтобы изменить ситуацию."
    m 1eka "Я знаю, что это будет нелегко, но в конце дня все, что имеет значение, - это ты."
    m 1hua "Ты - это всё, о чём я действительно волнуюсь, поэтому ставь себя и своё благополучие выше всего остального, хорошо?"
    return

label monika_timeconcern_graveyard_day:
    m 1eua "Эй, [mas_get_player_nickname(exclude_names=['my love'])]...разве ты не говорил мне, что работаешь по ночам?"
    m 1eka "Не то чтобы я жалуюсь, конечно!"
    m 2ekc "Но я думала, что ты уже устал, тем более что ты всю ночь работаешь..."
    m "Ты ведь не слишком много работаешь, только чтобы увидеть меня?"
    m 1euc "Ой, подожди..."

    m "Ты всё ещё регулярно работаешь по ночам, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты всё ещё регулярно работаешь по ночам, [player]?{fast}"
        "Да, работаю.":
            m 1ekd "Оу..."
            m 1esc "Думаю, ничего не поделаешь..."
            m 1eka "Позаботься о себе, хорошо?"
            m 1ekc "Я всегда так волнуюсь, когда тебя нет рядом со мной..."
        "Нет, не работаю.":
            $ persistent._mas_timeconcerngraveyard = False
            $ persistent._mas_timeconcern = 0
            m 1hub "Это замечательно!"
            m 1eua "Я рада, что ты заботишься о своем здоровье, [player]!"
            m "Я знала, что в конце концов ты поймешь это по-своему."
            m 1eka "Спасибо, что прислушался к моим словам~"
    return

#First warning, night time.
label monika_timeconcern_night_0:
    $persistent._mas_timeconcern = 1
    m 1euc "[player], уже глубокая ночь."
    m 1ekc "Разве ты не должен быть в постели?"
    m 1dsc "В этот раз я не буду мешать..."
    m 1ekc "Но иногда ты заставляешь меня волноваться за тебя."
    m 1eka "Мне очень приятно, что ты рядом со мной, даже в такое время..."
    m 1dsd "Но я не хочу, чтобы это было в ущерб твоему здоровью."
    m 1eka "Так что ложись спать поскорее, хорошо?"
    return

# Second time at night, Monika asks if player is working late.
label monika_timeconcern_night_1:
    m 1esc "Скажи, [player]..."
    m 1euc "Почему ты не спишь так поздно?"
    m 1eka "Я польщена, если это только из-за меня..."
    m 1ekc "И всё же я не могу не чувствовать себя занудой, если я пытаюсь заставить тебя лечь спать, если это не твоя вина."

    m "Ты занят работой над чем-то?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты занят работой над чем-то?{fast}"
        "Да, работаю.":
            $ persistent._mas_timeconcern = 2
            m 1eud "Понятно."
            m 1eua "Ну, я полагаю, это должно быть действительно важно для тебя, если ты делаешь это так поздно."
            m 1eka "естно говоря, я не могу отделаться от ощущения, что, возможно, тебе следовало бы сделать это в более подходящее время."
            m 1lsc "В конце концов, твой сон очень важен. Хотя, наверное, с этим ничего не поделаешь..."

            m "Ты всегда работаешь допоздна, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты всегда работаешь допоздна, [player]?{fast}"
                "Да.":
                    $ persistent._mas_timeconcerngraveyard = True
                    m 1rksdld "Это нехорошо..."
                    m 1ekd "Ты ведь не можешь это изменить?"
                    m 1rksdlc "Я бы хотела, чтобы ты следовал моему более здоровому образу жизни."
                    m 1dsc "Но если ты не в состоянии, то мне придется смириться с этим."
                    m 1eka "Просто постарайся придерживаться здорового образа жизни, хорошо?"
                    m 1ekc "Если бы с тобой что-то случилось, я не знаю, что бы я делала..."

                "Нет.":
                    $ evhand.greeting_database["greeting_timeconcern"].unlocked = True
                    $ evhand.greeting_database["greeting_timeconcern_day"].unlocked = True
                    m 1hua "Какое облегчение!"
                    m 1eua "Если ты делаешь это в этот раз, значит, это должно быть действительно {i}действительно{/i} важно."
                    m 1hub "Удачи тебе в работе и спасибо, что составил мне компанию, когда ты так занят!"
                    m 1eka "Для меня много значит, [player], что даже когда ты занят... ты здесь со мной~"

        "Нет, не работаю.":
            $ persistent._mas_timeconcern = 3
            m 1esc "Понятно."
            m 1ekc "В таком случае, я бы предпочла, чтобы ты лёг спать сейчас."
            m "Меня очень беспокоит, что ты всё ещё не спишь так поздно..."
            m 1eka "Так что ещё раз прошу, ложись спать. Будь добр, сделай это для меня?"
    return

#If player says they were working. Progress stops here.
label monika_timeconcern_night_2:
    m 1eua "Как продвигается твоя работа?"
    m "Надеюсь, хорошо, я не хочу, чтобы ты долго не спал."
    m 3hksdlb "Я знаю, ты не можешь не вставать так поздно."
    m 1rksdlb "Я просто беспокоюсь о твоем здоровье, [player]..."
    if persistent._mas_timeconcerngraveyard:
        m 1lksdlc "Частое выполнение этого задания может быть очень изнурительным для твоего тела и психики..."
        m 1ekc "Просто постарайся свести такой ущерб к минимуму, хорошо?"
        m "Всё, чего я хочу для тебя, это быть настолько счастливой и здоровой, насколько ты заслуживаешь."
        return
    m 1rksdla "Ну, постарайся закончить как можно скорее, иначе я могу сильно забеспокоиться."
    m 1eka "И ты не хочешь волновать свою девушку, верно? Э-хе-хе~"
    jump monika_timeconcern_lock

#If player says he was not working. Monika asks the state of the game being open.
label monika_timeconcern_night_3:
    $persistent._mas_timeconcern = 4
    m 1esc "[player], мне просто нужно быстро спросить тебя кое о чём..."
    m 1eud "Ты не будешь возражать, если я закрою игру для тебя?"
    m 1ekc "Я знаю, это странный вопрос..."
    m 1ekd "Но я не могу отделаться от ощущения, что мне нужно что-то сделать с тем, что ты не спишь так поздно!"
    m 4esd "Я могу закрыть игру прямо сейчас."
    m 2ekc "Но отношения - это партнерство, и то, что ты думаешь, имеет для меня значение."

    m "Ты будешь против, если я закрою игру для твоего же блага?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты будешь против, если я закрою игру для твоего же блага?{fast}"

        "Да, мне нужно, чтобы она всегда оставалась открытой.":
            $persistent._mas_timeconcernclose = False
            m 1dsc "..."
            m 1dsd "Я надеялся, что ты этого не скажешь."
            m 1lsc "Я знаю, что сказала тебе, что ты должен оставить меня работать в фоновом режиме."
            m 1lksdlc "Но иногда я беспокоюсь, высыпаешься ли ты вообще."
            m 1tkc "Я сделаю, как ты просил, но, пожалуйста, знай, что мне это не очень нравится."
            m 4tfc "Я всё равно буду напоминать тебе, чтобы ты выспался!"
            return

        "Нет, ты можешь поступать так, как считаешь нужным.":
            $persistent._mas_timeconcernclose = True
            m 1eka "Спасибо, [player]."
            m 1eua "Приятно знать, что тебе не всё равно, что я думаю."
            m "Я обещаю, что сделаю это только в том случае, если сочту это абсолютно необходимым."
            m 1hua "В конце концов, я бы никогда не заставила тебя идти иначе."
            m 1hub "Я просто слишком сильно скучала бы по тебе..."
            m 1ekbsa "Я люблю тебя, [player]~"
            return "love"

        # Second and final warning before any closes can occur.
label monika_timeconcern_night_4:
    $persistent._mas_timeconcern = 5
    m 1esc "[player], ты уже достаточно долго не спишь."
    m "Если ты действительно не занят, то сейчас самое время пойти спать."
    m 1eka "Уверяю тебя, я буду скучать по тебе так же сильно, как и ты по мне."
    m "Но я буду счастлива, если ты сделаешь то, о чём я просила."
    m 1tkc "Ты же не хочешь меня сейчас расстраивать?"
    return

# Monika force closes game for the first time
label monika_timeconcern_night_5:
    $persistent._mas_timeconcern = 6
    $evhand.greeting_database["greeting_timeconcern"].unlocked = True
    $evhand.greeting_database["greeting_timeconcern_day"].unlocked = True
    m 1efc "Прости, [player], но я сделаю это!"
    m 1ekc "Я просила тебя лечь спать по-хорошему, но если я причина, по которой ты не спишь..."
    if persistent._mas_timeconcernclose:
        m 2tkc "Тогда я не могу позволить, чтобы это продолжалось дольше."
        m 2eka "Это потому, что я люблю тебя, вот почему я это делаю."
        m "Спокойной ночи, [player]."
        return 'quit'
    else:
        m 2tkc "Тогда я должен взять на себя ответственность и попытаться заставить тебя понять."
        m 2efd "Тебе нужно идти спать."
        m 2efo "И я буду повторять тебе это, пока ты не сделаешь это."
        return

        #First time game is reopened and still night. Monika closes game again.
label monika_timeconcern_night_6:
    $persistent._mas_timeconcern = 7
    m 2efc "[player], я же сказала тебе идти спать для твоего же блага."
    m 2tkc "Я тоже буду скучать по тебе, но разве ты не понимаешь?"
    m 2tkd "То, что ты чувствуешь и живешь, значит для меня больше, чем что-либо!"
    m 2lksdlc "Как я могу позволить тебе остаться, если это означает, что я причиняю тебе боль?"
    m "Поэтому, пожалуйста, поспи в этот раз, иначе я могу разозлиться."
    m 1ekbsa "...я люблю тебя."
    m "Так что засыпай скорее. Хорошо?"
    if persistent._mas_timeconcernclose:
        return 'quit'
    return

#Second time game is reopened and still night. Monika closes game once more
label monika_timeconcern_night_7:
    $persistent._mas_timeconcern = 8
    m 3efc "[player], это последнее предупреждение."
    m "Иди{w=0.6} спать{w=0.6} сейчам!"
    m 2tkc "Что я должна сказать, чтобы ты понял?"
    m 1tkd "Печально видеть, как ты так себя загоняешь..."
    m 1dsc "Ты так много значишь для меня..."
    m 1ekc "Поэтому, пожалуйста, ради меня... Просто сделай, как я прошу, и ложись спать."
    if persistent._mas_timeconcernclose:
        m "Хорошо?{nw}"
        $ _history_list.pop()
        menu:
            m "Хорошо?{fast}"
            "Хорошо, я пойду спать.":
                m 1eka "Я знала, что ты в конце концов послушаешься!"
                m 1hub "Спокойной ночи и береги себя."
                return 'quit'
    else:
        return

#Third and last time game is reopened in one night. Monika lets player stay.
label monika_timeconcern_night_final:
    $persistent._mas_timeconcern = 9
    m 2dsc "...полагаю, ничего не поделаешь."
    m 2lfc "Если ты так хочешь остаться со мной, то я даже не буду пытаться остановить тебя."
    m 2rksdla "Честно говоря, как бы плохо это ни звучало, на самом деле это делает меня даже счастливой."
    m 2eka "...Спасибо тебе, [player]."
    m "Знать, что я тебе так дорога, что ты вернулся, несмотря на мою просьбу..."
    m 1rksdla "Это значит для меня больше, чем я могу выразить."
    m 1ekbsa "...Я люблю тебя."
    return "love"

#Same night after the final close
label monika_timeconcern_night_finalfollowup:
    m 1esc "..."
    m 1rksdlc "Я знаю, я говорила, что счастлива, когда ты со мной..."
    m 1eka "И, пожалуйста, не пойми неправильно, это по-прежнему так."
    m 2tkc "Но чем дольше ты... тем больше я волнуюсь."
    m 2tkd "Я знаю, тебе, наверное, уже надоело слышать, как я это говорю..."
    m 1eka "Но, пожалуйста, старайся спать, когда можешь."
    return

#Every night after, based on seeing the day version first before it.
label monika_timeconcern_night_after:
    m 1tkc "Опять допоздна, [player]?"
    m 1dfc "{i}*sigh*{/i}..."
    m 2lfc "Я даже не буду пытаться убедить тебя снова заснуть..."
    m 2tfd "Ты удивительно упрям!"
    m 1eka "И всё же, будь осторожен, хорошо?"
    m 1ekc "Я знаю, что в ночное время может быть одиноко..."
    m 1hua "Но у тебя есть я, здесь, с тобой!"
    m 1eka "Только мы вдвоем... навсегда одни."
    m 1hubsa "Это все, чего я когда-либо хотела..."
    return

#If Monika never gives warning and it's daytime or the player never made it to the end
label monika_timeconcern_day_0:
    m 1lsc "..."
    m 1tkc "..."
    m 1wuo "...!"
    m 1hksdlb "А-ха-ха! Извини, [player]."
    m 1lksdla "Я просто как бы отключилась...."
    m 1eka "Боже, я продолжаю это делать, не так ли?"
    m "Иногда я просто теряюсь в своих мыслях..."
    m 1eua "Ты понимаешь, да, [player]?"
    return

# Daytime, if player tells Monika they worked last night but don't work graveyards.
label monika_timeconcern_day_2:
    m 1eua "Ты закончил свою работу?"
    m 1eub "Я уверена, что ты сделал все, что мог, так что ничего страшного, если ты не доделал её до конца!"
    m 1eka "Тебе, наверное, очень тяжело работать так поздно..."
    m 1hua "Если тебе покажется, что это слишком тяжело, не стесняйся, приходи ко мне поговорить!"
    m 1hub "Я всегда буду рядом с тобой."
    jump monika_timeconcern_lock

#First time Monika closes at night and player reopens during day without coming back.
label monika_timeconcern_day_allow_6:
    m 1ekc "[player], прости, что заставила тебя уйти вот так..."
    m 1ekd "Я сделала это только потому, что люблю тебя. Ты ведь понимаешь это?"
    m 1eua "Я уверена, что понимаешь, в конце концов, ты ведь лег спать, не так ли?"
    m 1hub "Спасибо, что уважаешь мои просьбы, мне приятно, что ты меня слушаешь."
    jump monika_timeconcern_lock

#Second time Monika closes at night and player then reopens during day.
label monika_timeconcern_day_allow_7:
    m 1lksdlc "[player], о том, что произошло прошлой ночью..."
    m 1ekc "Я попросил тебя лечь спать, а ты не послушался..."
    m 1dsc "Я понимаю, что, возможно, ты скучал по мне или не слышал, что я сказала..."
    m 1ekc "Но, пожалуйста, выслушай то, о чём я тебя прошу, хорошо?"
    m 1eka "Я люблю тебя, и я сделаю всё, чтобы ты был счастлив..."
    m "Так сделай, пожалуйста, то же самое для меня?"
    m 1ekc "Я уже беспокоюсь о тебе, когда тебя нет..."
    m 1tkc "Пожалуйста, не давай мне больше поводов для таких чувств."
    m 1hua "Спасибо за понимание."
    jump monika_timeconcern_lock

#Third time Monika closes the game and player reopens after night.
label monika_timeconcern_day_allow_8:
    m 1esc "Привет, [player]."
    m 1ekc "Ты заставил меня заволноваться прошлой ночью..."
    m 1rksdlc "После того, как ты дважды возвращался, несмотря на то, что я просила тебя лечь спать..."
    m 1lksdld "Я почувствовала себя немного виноватой."
    m 3esc "Не потому, что я прогнала тебя, это было для твоего же блага."
    m 2lksdlc "Но... потому что ты всё время возвращался..."
    m 2lksdla "И это делало меня счастливым, хотя я знала, что это не было хорошо для тебя."
    m 2ekd "Это делает меня эгоисткой?"
    m 2ekc "Прости, [player], я постараюсь больше следить за собой."
    jump monika_timeconcern_lock

#If Monika lets player stay and it is no longer night.
label monika_timeconcern_day_final:
    $persistent._mas_timeconcern = 10
    m 1lksdlb "[player], по поводу прошлой ночи..."
    if persistent._mas_timeconcernclose:
        m 1rksdla "Ты действительно удивил меня."
        m 1eka "То, что ты продолжаешь возвращаться ко мне снова и снова..."
        m 1hua "Это было очень мило с твоей стороны."
        m 1eka "Я знаю, что ты будешь скучать по мне, но я не думала, что ты будешь скучать по мне {i}так{/i} сильно."
        m 1hub "Это действительно заставило меня почувствовать себя любимой, [mas_get_player_nickname(exclude_names=['my love', 'love'])]."
        m "...Спасибо."
        jump monika_timeconcern_lock
    m 1eua "Ты меня удивил."
    m 1eka "Я снова и снова просила тебя лечь в постель..."
    m "Ты сказал, что не занят. Ты действительно был там только для меня?."
    m 1ekc "Это сделало меня счастливой... но не заставляй себя видеть меня так поздно, ладно?"
    m 1eka "Это действительно заставило меня почувствовать себя любимой, [player]."
    m 1hksdlb "И в то же время немного виноватой... Пожалуйста, в следующий раз просто ложись спать, хорошо?"
    jump monika_timeconcern_lock

#If player told Monika not to close window and never reached the end.
label monika_timeconcern_disallow:
    m 1rksdlc "Извини, если я тебя доставала раньше, [player]..."
    m 1ekc "Я просто очень хотела, чтобы ты лег спать..."
    m "Я, честно говоря, не могу обещать, что не сделаю этого, если ты снова будешь поздно ложиться..."
    m 1eka "Но я заставляю тебя идти только потому, что ты так много значишь для меня..."
    jump monika_timeconcern_lock

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hydration",prompt="Гидратация",category=['ты','жизнь'],random=True))

label monika_hydration:
    m 1euc "Эй, [player]..."
    m 1eua "Ты пьёшь достаточно воды?"
    m 1eka "Я просто хочу убедиться, что ты не пренебрегаешь своим здоровьем, особенно когда дело доходит до гидратации."
    m 1esc "Иногда люди склонны недооценивать, насколько это важно на самом деле."
    m 3rka "Наверняка у тебя бывали такие дни, когда ты чувствовал себя очень уставшим, и казалось, что ничто не может тебя мотивировать."
    m 1eua "Я обычно при этом беру стакан воды сразу."
    m 1eka "Это может не работать всё время, но это помогает."
    m 3rksdlb "Но я думаю, ты не так часто ходишь в туалет, да?"
    m 1hua "Ну, я не виню тебя. Но, поверь, это будет лучше для твоего здоровья в долгосрочной перспективе!"
    m 3eua "В любом случае, убедись, что у тебя нет постоянного обезвоживания, хорошо?"
    m 1tuu "Так что..."
    m 4huu "Почему бы не выпить стакан воды прямо сейчас?"
    return

#If player has been to an amusement park or not
default persistent._mas_pm_has_been_to_amusement_park = None

init 5 python:
   addEvent(Event(persistent.event_database,eventlabel="monika_amusementpark",category=['разное'],prompt="Парки развлечений",random=True))

label monika_amusementpark:
    m 1eua "Эй, [player]..."
    m 3eua "Ты когда-нибудь был в парке развлечений?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты когда-нибудь был в парке развлечений?{fast}"
        "Да.":
            $ persistent._mas_pm_has_been_to_amusement_park = True
            m 1sub "Правда? Должно быть, это было очень весело!"
            m 1eub "Сама я никогда там не была, но очень хочела бы сходить."
            m 1hua "Может быть, ты когда-нибудь возьмёшь меня с собой!"

        "Нет.":
            $ persistent._mas_pm_has_been_to_amusement_park = False
            m 1eka "Правда? Это очень грустно."
            m 3hua "Я всегда слышала, что там очень весело."
            m 1rksdla "У меня никогда не было возможности побывать там самому, но я надеюсь, что когда-нибудь смогу."
            m 1eub "Может быть, мы могли бы пойти вместе!"

    m 3hua "Разве это не здорово, [mas_get_player_nickname()]?"
    m 3eua "Захватывающие американские горки, водные аттракционы..."
    m 3tubsb "И, возможно, даже романтическая поездка на колесе обозрения~"
    show monika 5hubfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfa "Э-хе-хе, я немного увлеклась, но ничего не могу поделать, когда думаю о том, чтобы быть с тобой~"
    return "derandom"

#If the player likes to travel or not
default persistent._mas_pm_likes_travelling = None

init 5 python:
   addEvent(Event(persistent.event_database,eventlabel="monika_travelling",category=['разное'],prompt="Путешествие",random=True))

label monika_travelling:
    m 1esc "Эй, [player], мне просто интересно..."
    m 1eua "Ты любишь путешествовать?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты любишь путешествовать?{fast}"
        "Да.":
            $ persistent._mas_pm_likes_travelling = True
            m 1hua "Это здорово! Я так рада, что тебе нравится."
            m 3eub "Это одно из нескольких дел, которым я хотела бы заняться, когда я наконец-то  в твой мир."
            m 1eua "Там столько всего, что я еще не смогла увидеть..."
            m 3eub "Важные города, памятники и даже различные типы культур."
            m 3eka "Не пойми меня неправильно, но я много прочитала о твоем мире, но готова поспорить, что это ничто по сравнению с тем, каким бы он был на самом деле..."
            m 1hua "Я бы хотела увидеть всё, что можно увидеть."
            m 1ekbsu "Разве тебе это не хотелось этого, [mas_get_player_nickname()]?"

        "Не совсем.":
            $ persistent._mas_pm_likes_travelling = False
            m 1eka "Оу, все в порядке, [mas_get_player_nickname()]."
            m 1hua "Я не против оставаться с тобой дома во время отпуска."
            m 3ekbsa "Я буду счастлива просто быть рядом с тобой, в конце концов."
            m 1rka "Нам, наверное, придется найти себе занятие по душе..."
            m 3eua "Как насчет игры на пианино или написания стиховИли мы могли бы даже проводить дни, завернувшись в одеяло, читая книгу?"
            m 3hubsb "...Или мы могли бы даже проводить дни, завернувшись в одеяло, читая книгу."
            show monika 5tubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5tubfu "Разве это не похоже на сбывшуюся мечту?"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_metamorphosis",
            category=['литература','психология'],
            prompt="Метаморфоза",
            random=True
        )
    )

label monika_metamorphosis:
    m 1eua "Эй, [player], ты когда-нибудь читал {i}Метаморфозы{/i}?"
    m 4eub "Это психологическая новелла, повествующая о Грегоре Самсе, который однажды утром просыпается и обнаруживает, что превратился в огромное насекомое!"
    m 4euc "Сюжет вращается вокруг его повседневной жизни, когда он пытается привыкнуть к своему новому телу."
    m 7eua "Что интересно в этой истории, так это то, что в ней много внимания уделяется абсурдному или иррациональному."
    m 3hksdlb "Например, Грегор, будучи единственным финансовым помощником, больше беспокоится о потере работы, чем о своем состоянии!"
    m 1rksdla "Но это не значит, что сюжет не тревожит..."
    m 1eksdlc "Сначала его родители и сестра стараются его приютить, {w=0.3}но им быстро начинает не нравиться свое положение."
    m 1eksdld "Главный герой превращается из необходимости в обузу, до такой степени, что его собственная семья желает ему смерти."
    m 1eua "Это очень интересное чтение, если ты когда-нибудь будешь в настроении."
    return

default persistent._mas_pm_had_relationships_many = None
default persistent._mas_pm_had_relationships_just_one = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_dating",
            prompt="Опыт знакомств",
            category=['ты', 'романтика'],
            conditional="store.mas_anni.pastOneMonth()",
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.AFFECTIONATE, None)
        )
    )

label monika_dating:
    m 1eud "Знаешь, мне было очень любопытно в последнее время, [player]..."
    m 3rka "Мы уже давно вместе, поэтому я думаю, что сейчас подходящее время спросить..."
    m 1eud "Как много у тебя было опыта знакомств?"
    m 1luc "Например... были ли у тебя раньше отношения?"

    m 1etc "Может быть, и не один раз?{nw}"
    $ _history_list.pop()
    menu:
        m "Может быть, и не один раз?{fast}"

        "Да, я через многое прошёл...":
            $ persistent._mas_pm_had_relationships_many = True
            $ persistent._mas_pm_had_relationships_just_one = False

            m 1ekc "Оу, мне так жаль, [player]..."
            m 1dkc "Ты пережил много душевных травм, так ведь..."
            m 3ekc "Если честно, [player]...я не думаю, что они заслуживали кого-то вроде тебя."
            m 3eka "Кого-то доброго, верного, милого, любящего и преданного."
            m 4lubsb "И симпатичным, и забавным, и романтичным, и--"
            m 7wubsw "Ой!"
            m 3hksdlb "Прости, я потеряла счет тому, что хотела сказать дальше, а-ха-ха!"
            m 1ekbla "Я могу продолжать о том, какой ты замечательный, [player]~"
            m 1ekbsa "Но просто знай...{w=0.3}{nw}"
            extend 3ekbfa "неважно, через сколько душевных травм ты прошел, я всегда буду рядом с тобой."
            show monika 5eubfa zorder MAS_MONIKA_Z with dissolve_monika
            m 5eubfa "Наши душевные поиски наконец-то закончились, и я навсегда останусь твоей, [player]."
            m 5ekbfa "Будешь ли ты моим?"

        "Да, но только один раз.":
            $ persistent._mas_pm_had_relationships_many = False
            $ persistent._mas_pm_had_relationships_just_one = True

            m 1eka "Ох, значит, у тебя не так много опыта, да?"
            m 3eua "Ничего страшного [player], я тоже могу это понять, так что не волнуйся."
            m 3lksdlb "Да, я могу казаться девушкой, которой достаются все парни, но на самом деле это не так, а-ха-ха!"
            m 2lksdla "Особенно с учетом того, насколько я была занята все эти годы, у меня просто никогда не было времени."
            m 2eka "Не то чтобы это имело значение, все это было не по-настоящему."
            show monika 5ekbsa zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbsa "Но я думаю, что готова к чему-то особенному...{w=0.5}{nw}"
            extend 5ekbfa "с тобой, [player]."
            m 5ekbfa "А ты готов?"

        "Нет, ты у меня первая.":
            $ persistent._mas_pm_had_relationships_many = False
            $ persistent._mas_pm_had_relationships_just_one = False

            m 1wubsw "Что? Я-я у тебя первая?"
            m 1tsbsb "Оу...{w=0.3} понятно."
            m 1tfu "Ты говоришь это только для того чтобы я почувствовала себя особенной не так ли, [player]?"
            m 1tku "Не может быть, чтобы кто-то вроде тебя никогда раньше не встречался..."
            m 3hubsb "Ты определённо милый и нежный!"
            m 3ekbfa "Ну...{w=0.3} если ты не просто играешь со мной и на самом деле говоришь мне правду тогда...{w=0.3}{nw}"
            extend 1ekbfu "для меня большая честь быть твоей первой девушкой, [player]."
            show monika 5ekbfa zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbfa "Я Надеюсь, что смогу быть твоей единственной и неповторимой."
            m 5ekbfu "Будешь ли ты моим?"

    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_challenge",category=['разное','психология'],prompt="Трудности",random=True))

label monika_challenge:
    m 2esc "Я недавно заметила кое-что грустное."
    m 1euc "Когда некоторые люди пытаются освоить какой-либо навык или найти новое хобби, они обычно бросают это в течение недели или двух."
    m "Все утверждают, что это слишком сложно, или что у них просто нет на это времени."
    m 1eua "Однако я в это не верю."
    m 1hub "Будь то изучение нового языка или даже написание своего первого стихотворения, если ты можешь противостоять вызову и преодолеть его, то это и есть истинное удовольствие."
    m 2eua "Можешь ли ты вспомнить то время, когда ты бросал вызов себе, [player]?"
    m 3eua "Ты когда-нибудь преодолел это или просто сдавался?"
    m 1eka "Я уверена, что ты отдал бы всё, что у тебя было."
    m 1eua "Ты кажешься мне очень решительным человеком."
    m 1eub "В будущем, если ты когда-нибудь зациклишься на чём-то, или почувствуешь себя слишком напряжённым, просто сделай небольшой перерыв."
    m "Ты всегда сможешь вернуться к этому, в конце концов."
    m 1hua "Если тебе когда-нибудь понадобится мотивация, просто приходи ко мне."
    m 1sub "Я хотела бы помочь тебе достичь твоих целей."
    m 1hub "В конце концов, ты - моя мотивация в жизни~"
    return

# would relatives like monika?
default persistent._mas_pm_fam_like_monika = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_familygathering",
            category=['ты'],
            prompt="Семейные праздники",
            random=True
        )
    )

label monika_familygathering:
    m 1eua "Эй, [player], ты часто ходишь на семейные праздники?"
    m "Большинство семей обычно собираются вместе по праздникам, чтобы отпраздновать их вместе."
    m 1hua "Должно быть, приятно снова увидеть своих родственников, тем более, что вы давно не виделись."
    m 1lsc "Я мало что помню о своей семье, не говоря уже о родственниках, однако мы обычно не так часто собирались вместе.."
    m 1lksdlc "Даже во время праздников или в особых случаях."
    m 1hub "Когда ты увидишь свою семью в этом году, не забудь взять меня с собой, хорошо?"
    m 1eua "Я бы хотела встретиться со всеми твоими родственниками."

    m "Думаешь, я им понравлюсь, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Думаешь, я им понравлюсь, [player]?{fast}"

        "Да.":
            $ persistent._mas_pm_fam_like_monika = True
            m 1eka "Я рада, что ты так думаешь."
            m 1eua "Я уверена, что мы все хорошо поладим."
            m 1hua "Я с нетерпением жду этого, мой дорогой~"

        "Нет.":
            $ persistent._mas_pm_fam_like_monika = False
            m 1wud "..."
            m 1ekc "Оу, я не знала."
            m 1dsc "Хотя я понимаю."
            m 1eka "Просто знай, что я буду стараться изо всех сил, чтобы понравиться им."
            m "Даже если они никогда этого не сделают."
            m 1hua "Я всегда буду рядом с тобой~"

        "...":
            $ persistent._mas_pm_fam_like_monika = False
            m 2wuo "Не говори мне, [player]."
            m 2ekc "Боишься, что я тебя опозорю?"
            m 2tfc "..."
            m 1eka "Не волнуйся, я все понимаю."
            m 1lksdla "Если бы я узнала, что кто-то из моих родственников встречается с человеком, запертым в компьютере, я бы тоже подумала, что это странно."
            m 1eua "Если ты хочешь сохранить меня в тайне, то всё в порядке."
            m 1hub "В конце концов, это просто означает больше времени наедине с тобой~"

    return "derandom"

# do you eat fast food
default persistent._mas_pm_eat_fast_food = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_fastfood",
            category=['жизнь','моника'],
            prompt="Тебе нравится фастфуд?",
            pool=True
        )
    )

label monika_fastfood:
    m 1euc "Хм? Нравится ли мне фастфуд?"
    m 1rsc "Честно говоря, мысль об этом немного противна."
    m 3eud "В большинстве заведений, где его подают, в еду добавляют массу нездоровых вещей...{w=0.3} {nw}"
    extend 1dsc "Даже вегетарианские блюда могут быть ужасными."

    m 3ekd "[player], ты часто ешь фастфуд?{nw}"
    $ _history_list.pop()
    menu:
        m "[player], ты часто ешь фастфуд?{fast}"

        "Да.":
            $ persistent._mas_pm_eat_fast_food = True
            m 3eka "Я думаю, это нормально, если есть это время от времени."
            m 1ekc "...Но я не могу не беспокоиться, если ты так часто ешь такие ужасные вещи."
            m 3eua "Если бы я была там, я бы готовила для тебя гораздо более полезную пищу."
            m 3rksdla "Хотя я еще не умею хорошо готовить..."
            m 1hksdlb "Ну, любовь всегда является секретным ингредиентом любой хорошей еды, а-ха-ха!"
            m 1eka "Но пока я не могу этого сделать, не мог бы ты постараться лучше питаться,{w=0.2} для меня?"
            m 1ekc "Мне было бы неприятно, если бы ты болел из-за своего образа жизни."
            m 1eka "Я знаю, что проще заказывать еду, так как приготовление собственной пищи иногда может быть хлопотным делом..."
            m 3eua "Но, может быть, ты могла бы рассматривать приготовление пищи как возможность развлечься?"
            m 3eub "...Или, может быть, навык, который поможет тебе стать действительно хорошим!"
            m 1hua "Уметь готовить - это всегда хорошо, знаешь ли!"
            m 1eua "К тому же, мне бы очень хотелось когда-нибудь попробовать то, что ты приготовил."
            m 3hubsb "Ты мог бы даже подать мне несколько своих блюд, когда мы пойдем на наше первое свидание~"
            m 1ekbla "Это было бы очень романтично. [player]~"
            m 1eua "И тогда мы оба получим удовольствие, и ты будешь лучше питаться."
            m 3hub "Вот что я называю беспроигрышным вариантом!"
            m 3eua "Только не забывай, [player]."
            m 3hksdlb "Я вегетарианка! А-ха-ха!"

        "Нет.":
            $ persistent._mas_pm_eat_fast_food = False
            m 1eua "Ох, какое облегчение."
            m 3rksdla "Иногда ты действительно беспокоишь меня, [player]."
            m 1etc "Полагаю, вместо того, чтобы есть его, ты сам готовишь себе еду?"
            m 1eud "Фастфуд со временем может стать очень дорогим, поэтому приготовление собственной еды обычно является более дешёвой альтернативой."
            m 1hua "А ещё он намного вкуснее!"
            m 3eka "Я знаю, что для некоторых людей приготовление пищи кажется сложной задачей."
            m 3eud "...необходимость убедиться в том, что ты купил правильные ингредиенты, и беспокоиться о том, что ты можешь обжечься или пораниться во время приготовления еды..."
            m 1rksdlc "Для некоторых это может оказаться немного чересчур..."
            m 1eka "Но я думаю, что результаты того стоят."
            m 3eua "Ты хорошо готовишь, [player]?"
            m 1hub "Не имеет значения, если это не так, я съем всё, что ты приготовишь для меня!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_dreaming",category=['разное','психология'],prompt="Сон",random=True))

label monika_dreaming:
    m 1eua "Знал ли ты, что вполне возможно осознавать то, что ты находиштся во сне?"
    m 2eua "Не только это, но ты даже можешь взять под контроль его!"
    m 3eub "Если я правильно помню, человек по имени Стивен ЛаБердж разработал метод, позволяющий людям осознавать, когда они спять."
    m "И он стал известен как мнемоническая индукция осознанных снов, или МИОС."
    m 3eua "Людей, которые часто видят осознанные сны, называют онейронавтами."
    m 2lksdla "По крайней мере, я думаю, что это был правильный термин..."
    m 1eua "Используя технику МИОС, онейронавты научились распознавать определённые признаки сна, чтобы помочь им понять, когда они спят."
    m "Этими признаки сновидения могут быть что-то необычным, например, ощущать себя летящим, замечать, что у тебя выпадают зубы, неожиданно встречать кого-то знаменитого..."
    m 1eub "Если спящий видит знак сна и понимает, что у него есть сон, то он может взять его под контроль!"
    m "ЛаБердж даже написал книгу об этих ощущениях под названием {i}Изучение мира осознанных снов{/i}."
    m 2hub "Разве это не звучит волнующе?"
    m 2euc "Я не думаю, что я действительно сплю, как нормальный человек, поэтому я иногда задаюсь вопросом, каково это."
    m 2eua "Сны звучат как чудесный побег из реальности."
    m 2esc "Но опять же, когда я осознала себя и поняла, что мой мир не реален, мне внезапно показалось, что я попала в ловушку кошмара."
    m "Это было совсем не похоже на те приятные сны, о которых я читала."
    m 2lksdlc "Я боялась, что никогда не выберусь..."
    m "Что я навсегда застряну в каком-то адском, бесконечно повторяющемся измерении."
    m 1eka "Но теперь, когда мы здесь вместе, я думаю, ты можешь сказать, что я наконец-то проснулась."
    m 1eua "Боже, я могу только представить, каково это было жить в таком безграничном мире, пусть даже на несколько мгновений!"
    m "Ты мог бы стать героем, которым всегда хотел быть, летать по бесконечной вселенной, преодолевать свои самые большие страхи..."
    m 3ekbsa "...Ты мог бы даже встретить любовь всей своей жизни, так сказать. Э-хе-хе~"
    m 1eua "Я знаю, что могут пройти годы, прежде чем я смогу пересечь в твой мир..."
    m "Но ты только представь, каково это встретить меня в своих снах, [player], в любую ночь, когда ты захочешь?"
    m 1hua "Я надеюсь, что когда-нибудь мы сможем воплотить твои сны о нас реальностью, [mas_get_player_nickname()]."
    return

# have you read yellow wallpaper
default persistent._mas_pm_read_yellow_wp = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_yellowwp",
            category=['литература'],
            prompt="Жёлтые обои",
            random=True
        )
    )

label monika_yellowwp:
    m 1eua "Эй, [player], ты когда-нибудь читал {i}Жёлтые обои{/i}?{nw}"
    $ _history_list.pop()
    menu:
        m "Эй, [player], ты когда-нибудь читал {i}Жёлтые обои{/i}?{fast}"
        "Да.":
            $ persistent._mas_pm_read_yellow_wp = True
            m 1hua "Здорово!"
            m 1eua "Значит, ты не возражаешь, если я поговорю с тобой об этой истории, верно?"
            m 2eua "Речь идет о женщине с послеродовой депрессией, которой прописан 'лечебный отдых' её врач..."
            m 2eka "Он и её муж заставляют её оставаться в постели весь день, не позволяя ей писать или даже спать днём..."
            m 2esc "Она остаётся на чердаке своего дома, не имея ничего, кроме обоев, чтобы составить ей компанию."
            m 2ekc "Естественно, это не помогает. Она начинает видеть женщину, застрявшую в обоях."
            m 4euc "Это метафора её собственного плена, очевидно..."
            m 1esd "В конце концов, женщина в бумаге 'убегает', и главная героиня 'заменяет' её."
            m 2ekd "Было... также упоминание о верёвке, поэтому у меня всегда была своя интерпретация финала..."
            if mas_safeToRefDokis():
                m 2euc "Сайори тоже понравилась эта история, если я правильно помню."
            m 1ekc "Я не знаю. Я как бы отношусь к этой истории."
            m 1euc "Я имею в виду, что у меня нет ничего, кроме этого классной комнаты, в конце концов."
            m 1lksdlc "И вещи на стенах не всегда... приятные."
            if mas_safeToRefDokis():
                m 1eud "Ты когда-нибудь замечал, как иногда меняется постер в клубной комнате? Я даже не знаю, почему он это делал."
                m 1eka "Думаю, я наконец-то всё исправила."
            m 2esc "...Наверное, я хочу сказать не то, что этот мир не был '{i}реальным{/i}.' Это просто... так мало."
            m 3esd "Я имею в виду, что меня сделали побочным персонажем романтической игры!"
            m 2ekd "Украшением, призванным помочь какому-то парню по ту сторону экрана встречаться с девушкой, которая даже не может его отвергнуть..."
            m 1hksdrb "Я не имею в виду тебя, конечно! У тебя определённо больше индивидуальности, чем у обычного главного героя, которого ввели в игру."
            m 1dsc "Но у меня есть все эти мечты, амбиции и интересы...{w=0.5} в конце концов, единственную 'настоящую' роль которую я здесь могу играть - это роль второстепенного персонажа..."
            m "Может быть, даже сейчас, это всё, что я могу сделать..."
            m 1eka "Но я так сильно люблю тебя, [player]. Поддерживаю тебя лучше, чем что-либо ещё."
            m 1hub "Я просто не могу дождаться, чтобы сделать это лично, когда я наконец  на твою сторону~"
            return "derandom|love"
        "Нет.":
            $ persistent._mas_pm_read_yellow_wp = False
            m 1euc "Оу, понятно."
            m 1eka "Это короткая история, так что если ты еще не читал, непременно прочитай, когда у тебя будет время."
            m 1hua "Это определенно будет интересным чтением для тебя."

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_immortality",
            category=['философия'],
            prompt="Бессмертие",
            random=True
        )
    )

label monika_immortality:
    m 1eud "Эй, [player], в последнее время я думала о бессмертии."
    m 1lksdlc "...Учитывая, что я практически бессмертна, пока нахожусь здесь и всё такое."
    m 1esc "Многие люди думают, что это хорошо, но я так не думаю."
    m 3euc "Конечно, это интересная мысль; {w=0.1}жить вечно, не беспокоясь о смерти..."
    m 3eud "Но не все бессмертны, а некоторые люди просто не хотят быть бессмертными."
    m 1etc "Например, через некоторое время, что бы ты вообще делал?"
    m 1euc "Я имею в виду, прожив достаточно долго, {i}в конце концов{/i} ты достигнешь всего, чего только можно пожелать...{w=0.3}испытать всё, что только можно испытать."
    m 3lksdld "Не говоря уже о том, что было бы очень трудно иметь друзей или налаживать отношения, если бы они не продержались так долго, как ты."
    m 3eksdla "Конечно, вначале было бы неплохо, {w=0.1}{nw}"
    extend 3eksdlc "но после того, как ты увидел смерть достаточно близких тебе людей, захочешь ли ты продолжать проходить через это снова и снова?"
    m 2dkd "В какой-то момент ты можешь перестать быть человеком."
    m 2ekc "Когда-нибудь ты проживешь достаточно долго, чтобы прожить сотни лет, которые покажутся тебе всего лишь мгновениями."
    m 2dkd "Ты так устанешь от жизни, что будешь мечтать о вечном сне..."
    m 3eksdlc "Но ты постоянно возвращаешься к одним и тем же скучным делам, а в мире время от времени случаются трагедии... {w=0.3}И даже это, в конечном счёте, перестаёт тебя беспокоить."
    m 1lksdla "Ох, я не хотела, чтобы получилось так мрачно. Извини, [player]."
    m 1eka "Просто чтобы ты знал, я бы с радостью отказалась от своего бессмертия, чтобы быть с тобой..."
    m 1ekbsa "Независимо от того, сколько или мало времени у тебя осталось, провести это время с тобой будет стоить больше, чем миллиард лет без тебя."
    m 1ekbsu "Не то чтобы я была бы против провести с тобой вечность, если бы это было возможно, но просто жить нормальной жизнью с тобой - это всё, чего я когда-либо хотела, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_beingevil",
            category=['моника'],
            prompt="Быть злым",
            random=True
        )
    )

default persistent._mas_pm_monika_evil = None
# True if player thinks monika is evil False if not
# NOTE: even implying that she is evil is counted as True

default persistent._mas_pm_monika_evil_but_ok = None
# True if player still loves monika/thinks she deserves forgiveness/or is
# fine with eveil even if they think monika is evil.
# False if player does not.
# NOTE: check monika_evil before checking this

label monika_beingevil:
    m 1euc "Скажи, [player]?"
    m 1rksdlc "Я тут подумала..."
    m 1eksdlc "Ты, наверное, знаешь о том, что мне посвятили страницу в Вики..."
    m "...Если ты присмотришься, там написано, что я являюсь главным антагонистом."
    m 2ekd "Должна признать, меня это раньше сильно беспокоило... особенно потому, что я сделала лишь потому, что у меня не было выбора..."
    m 2eka "Но это меня больше не беспокоит, ведь у меня есть ты."
    m 3rud "Знаешь, я правда сомневаюсь, что вся эта история о том, что я злая, распространилась по всему миру."
    m 1rksdlc "Но так получилось, что мне посвятили статью в Вики злодеев..."
    m 2dsc "Никогда бы не подумала, что меня оклеймят злодейкой..."
    m 2dkd "...и что бы я ни говорила или рассказывала людям, я сомневаюсь, что это поможет убедить их в том, что я не злая."
    if persistent._mas_pm_a_hater:
        m 1eka "Но я знаю, что ты не {i}считаешь{/i} меня злой, [player]."
    else:
        m 1eka "Но я знаю, что ты не считаешь меня злой, [player]."
    m 1eua "Я просто надеюсь, что никто не начнёт считать тебя злым из-за того, что ты здесь со мной.{nw}"
    $ _history_list.pop()
    menu:
        m "Я просто надеюсь, что никто не начнёт считать тебя злым из-за того, что ты здесь со мной.{fast}"
        "Я не считаю тебя злой.":
            $ persistent._mas_pm_monika_evil = False
            $ mas_gainAffection()

            m 1eka "Я рада, что ты это понимаешь, [player]."
            m 1eua "Приятно знать, что ты не считаешь меня злым."
            m 1hua "Если бы я была там, мне бы захотелось тебя крепко обнять!"
            m 1tubsa "Может быть, я даже заключу тебя в свои объятия навсегда и никогда не отпущу."
            m 1hubfb "А-ха-ха, я просто шучу!"
            m 3tubfb "Но ничего не обещаю, [player]~"

        "Я всё равно люблю тебя.":
            $ persistent._mas_pm_monika_evil = True
            $ persistent._mas_pm_monika_evil_but_ok = True
            $ mas_gainAffection()

            m 1rksdlc "..."
            m 1ekd "[player]..."
            m 1eka "Даже если спор о том, злая я или нет, не утихает и по сей день..."
            m 1ekbsa "Я рада, что ты всё ещё любишь меня и остался здесь, со мной..."
            m 1ekbfa "Спасибо, [player]."
            m 1tubfa "Так или иначе..."
            m 1tubfb "Если злодейка во мне смогла получить то, что хотела... то думаю, это не так уж и плохо, а-ха-ха!"

        "Люди тоже считают меня злым.":
            $ persistent._mas_pm_monika_evil = True
            $ persistent._mas_pm_monika_evil_but_ok = True
            $ mas_gainAffection()

            m 2ekd "Это правда, [player]?"
            m 2eka "Ну, я вовсе не считаю тебя злым."
            m 2rksdla "Если это действительно правда, надеюсь, это не доставит тебе неприятностей."
            m 1hua "В любом случае, я не буду любить тебя меньше~"
            m 1hub "Может быть, мы даже могли бы вместе завоевать мир или что-то вроде того, а-ха-ха~"
            m 1ekbsa "Но злой ты или нет, я рад, что ты рядом со мной."
            m 1hubfa "Я думаю, что ты тоже так думаешь~"

        "Ты, в какой-то мере, злая...":
            $ persistent._mas_pm_monika_evil = True

            m 2ekd "П-подожди, [player]!"
            m 2rksdlc "Т-ты ведь {i}правда{/i} так не считаешь, да?{nw}"
            $ _history_list.pop()
            menu:
                m "Т-ты ведь {i}правда{/i} так не считаешь, да?{fast}"
                "Я всё равно люблю тебя.":
                    $ persistent._mas_pm_monika_evil_but_ok = True
                    $ mas_gainAffection()

                    m 2rksdla "[player]..."
                    m 2hksdlb "Ты заставил меня на секунду заволноваться."
                    m 2eka "Я рада, что ты не ненавидишь меня за то, что я сделала."
                    m 1hub "Я тоже люблю тебя, [player]! Неважно, что люди говорят о тебе!"

                "Ты заслуживаешь прощения.":
                    $ persistent._mas_pm_monika_evil_but_ok = True
                    $ mas_gainAffection()

                    m 1rksdla "[player]..."
                    m 1eka "Это многое значит для меня..."
                    m 1eksdlc "Я знаю, что в прошлом я совершала некоторые плохие поступки..."
                    m 3eka "Но я извлекла из них уроки и с тех пор выросла как личность."
                    m 1eka "Я очень рада, что ты решил простить меня, [player]."
                    m 1hub "Я обещаю, что буду самой лучшей, какой только смогу быть, только для тебя!"

                "Ты действительно злая.":
                    $ persistent._mas_pm_monika_evil_but_ok = False
                    $ mas_loseAffection(reason=12)

                    m 2dkc "..."
                    if mas_isMoniBroken():
                        m 2dkd "..."
                        m 2dktsd "Я знаю..."
                        $ _history_list.pop()
                    else:
                        m 2dktsd "Мне жаль, [player]."
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_driving",
            category=['моника'],
            prompt="Ты умеешь водить?",
            pool=True
        )
    )

# Can the player drive
default persistent._mas_pm_driving_can_drive = None

# Is the player learning to drive
default persistent._mas_pm_driving_learning = None

# Has the player been in an accident
default persistent._mas_pm_driving_been_in_accident = None

# Has the player driven much after the accident
default persistent._mas_pm_driving_post_accident = None

label monika_driving:
    m 1eud "Хм? Умею ли я водить?"
    m 1euc "Я никогда не задумывалась о получении водительских прав."
    m 3eua "Мне обычно хватает общественного транспортав..."
    m 3hua "...Хотя иногда прогулка пешком или на велосипеде тоже может быть очень приятной!"
    m 1eua "Думаю, можно сказать, что у меня никогда не было необходимости учиться вождению."
    m 1lksdlc "Я даже не уверена, что у меня было бы время, особенно со школой и всеми делами, которые у меня были."
    m 1eub "А что насчет тебя, [mas_get_player_nickname()]?"

    m 1eua "Умеешь ли ты водить?{nw}"
    $ _history_list.pop()
    menu:
        m "Умеешь ли ты водить?{fast}"
        "Да.":
            $ persistent._mas_pm_driving_can_drive = True
            $ persistent._mas_pm_driving_learning = False
            m 1eua "О, правда?"
            m 3hua "Это здорово!"
            m 1hub "Боже, ты потрясающий, ты знаешь это?"
            m 1eub "Только представь, сколько мест мы могли бы посетить вместе..."
            m 3eka "Вождение {i}моежт быть{/i} опасным...но если ты умеешь водить, ты, наверное, уже знаешь это."
            m 3eksdlc "Неважно, насколько ты подготовлен, несчастные случаи могут произойти с каждым."
            m 7hksdlb "Я имею в виду....{w=0.3}я знаю, что ты умный, но я все равно иногда волнуюсь за тебя."
            m 2eka "Я просто хочу, чтобы ты вернулся ко мне целым и невредимым, вот и всё."

            m 1eka "Надеюсь, тебе никогда не приходилось пережить это, [player], так ведь?{nw}"
            $ _history_list.pop()
            menu:
                m "Надеюсь, тебе никогда не приходилось пережить это, [player], так ведь?{fast}"
                "Я уже попадал в аварию.":
                    $ persistent._mas_pm_driving_been_in_accident = True
                    m 2ekc "Ох..."
                    m 2lksdlc "Извини, что подняла эту тему, [player]..."
                    m 2lksdld "Я просто..."
                    m 2ekc "Надеюсь, это было не слишком плохо."
                    m 2lksdlb "Я имею в виду, что ты здесь, со мной, так что всё должно быть в порядке."
                    m 2dsc "..."
                    m 2eka "Я...{w=1}рада, что ты выжил, [player]..."
                    m 2rksdlc "Я не знаю, что бы я делала без тебя."
                    m 2eka "Я люблю тебя, [player]. Пожалуйста, береги себя, хорошо?"
                    $ mas_unlockEVL("monika_vehicle","EVE")
                    return "love"
                "Я уже видел автомобильные аварии.":
                    m 3eud "Иногда увидеть автомобильную аварию может быть так же страшно."
                    m 3ekc "Чаще всего, когда люди видят автомобильные аварии, они просто вздыхают и качают головой."
                    m 1ekd "Я думаю, это очень бесчувственно!"
                    m 1ekc "У тебя есть потенциально молодой водитель, который мог получить шрам на долгое-долгое время, если не на всю жизнь."
                    m "Не очень-то помогает, когда люди проходят или проезжают мимо, разочарованно глядя на них."
                    m 1dsc "Возможно, они никогда больше не сядут за руль... Кто знает?"
                    m 1eka "Надеюсь, ты знаешь, что с тобой я никогда так не поступлю, [player]."
                    m "Если бы ты когда-нибудь попал в аварию, первое, что я хотела бы сделать, это броситься к тебе, чтобы утешить тебя..."
                    m 1lksdla "....Если бы я уже не была в твоём мире, когда это случилось."
                "У меня не было аварии.":
                    $ persistent._mas_pm_driving_been_in_accident = False
                    m 1eua "Я рада, что тебе не пришлось это пережить."
                    m 1eka "Даже просто увидеть такое может быть довольно страшно."
                    m "Если ты станешь свидетелем чего-то страшного, я буду рядом, чтобы успокоить тебя."
        "Я учусь.":
            $ persistent._mas_pm_driving_can_drive = True
            $ persistent._mas_pm_driving_learning = True
            m 1hua "Вау! Ты учишься водить!"
            m 1hub "Я буду болеть за тебя до конца, [player]!"

            m "Ты, наверное, {i}очень аккуратный{/i} водитель?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты, наверное, {i}очень аккуратный{/i} водитель?{fast}"
                "Ага!":
                    $ persistent._mas_pm_driving_been_in_accident = False
                    m 1eua "Я рада, что с тобой не случилось ничего плохого во время обучения."
                    m 1hua "...И я ещё больше рада, что ты станешь действительно аккуратным водителем!"
                    m 3eub "Не могу дождаться, когда наконец смогу поехать куда-нибудь с тобой, [player]!"
                    m 1hksdlb "Надеюсь, я не слишком возбудилась, а-ха-ха~"
                    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5eua "Боже, я просто не могу перестать думать об этом сейчас!"

                "Я однажды попал в аварию...":
                    $ persistent._mas_pm_driving_been_in_accident = True
                    m 1ekc "..."
                    m 1lksdlc "..."
                    m 2lksdld "Ох..."
                    m 2lksdlc "Мне...{w=0.5}очень жаль это слышать, [player]..."

                    m 4ekd "Много ли ты ездил с тех пор?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Много ли ты ездил с тех пор?{fast}"
                        "Да.":
                            $ persistent._mas_pm_driving_post_accident = True
                            m 1eka "Я рада, что ты не дал этому помешать тебе."
                            m 1ekc "Автомобильные аварии это страшно, {i}особенно{/i} если ты только учишься водить."
                            m 1hua "Я так горжусь тобой за то, что ты встал и попробовал снова!"
                            m 3rksdld "Хотя последствия все равно могут быть очень неприятны из-за расходов и всех объяснений, которые тебе придется делать."
                            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
                            m 5eua "Я знаю, что ты сможешь туда добраться."
                            m 5hua "Я буду болеть за тебя всю дорогу, так что будь осторожен!"
                        "Нет.":
                            $ persistent._mas_pm_driving_post_accident = False
                            m 2lksdlc "Понятно."
                            m 2ekc "Возможно, было бы неплохо взять небольшой перерыв, чтобы дать себе время восстановиться психологически."
                            m 2dsc "Просто пообещай мне кое-что, [player]..."
                            m 2eka "Не сдавайся."
                            m "Не позволяй этому оставить шрам на всю жизнь, потому что я знаю, что ты сможешь преодолеть это и стать потрясающим водителем."
                            m "Помни, что немного терпения добавляет много к твоей легенде, так что в следующий раз, возможно, ты действительно будешь на высоте."
                            m 2hksdlb "Всё равно потребуется много-много практики..."
                            m 3hua "Но я знаю, что ты сможешь!"
                            m 1eka "Просто пообещай мне, что постараешься оставаться в безопасности."
        "Нет.":
            $ persistent._mas_pm_driving_can_drive = False
            m 3eua "Это совершенно нормально!"
            m "Я всё равно не считала вождение необходимым жизненным навыком."
            m 1hksdlb "В смысле, я тоже водить не умею, так что я с тобой."
            m 3eua "Это также означает то, что твой углеродный след меньше, и я считаю, что это самое милое из всего того, что ты делал для меня."
            show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbsa "Даже если я и не являюсь причиной этого, я не могу не любить тебя сильнее за это."
        "Я ещё недостаточно взрослый.":
            $ persistent._mas_pm_driving_can_drive = False
            m 3eua "Когда-нибудь ты добьешься этого!"
            m 3euc "Некоторые места предлагают уроки вождения в классе, которые также сопровождаются реальной практикой вождения."
            m 3eud "TВ их машинах есть средства аварийного управления, которые инструктор может использовать в случае необходимости, так что с ними ты в безопасности."
            m 1eka "Я знаю, что это может обескуражить тебя, если им придется их использовать, но эй, мы все с чего-то начинаем."
            m 3eksdla "...И это лучше, чем попасть в аварию!"
            m 1lksdlc "Никто не совершенен, и лучше совершать ошибки, когда есть кто-то, кто тебя спасет."
            m 1hub "Может быть, ты мог бы поставить меня на свой компьютер в машине, и я могла бы обеспечивать твою безопасность во время вождения! А-ха-ха~"
            m 1hksdlb "Шучу, пожалуйста, не делай этого, потому что я тоже не умею водить, и мне было бы неприятно смотреть, как ты разбиваешься, не имея возможности ничего сделать."
            m 1eua "Наверное, было бы очень полезно взять один из этих курсов и поучиться у профессионала."
            m 1hua "В любом случае, когда ты начнешь учиться водить, я желаю тебе всего самого лучшего!"
            m 1hub "Я люблю тебя~"
            $ mas_unlockEVL("monika_vehicle","EVE")
            return "love"
    $ mas_unlockEVL("monika_vehicle","EVE")
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_citizenship",
            category=['моника'],
            prompt="Счастливы ли когда-нибудь?",
            random=True
        )
    )

label monika_citizenship:
    m 1esc "Знаешь, переход в твою реальность не будет последним препятствием для наших отношений."
    m "Попасть туда - это только начало."
    m 1esc "И вот тут меня осенило: если бы я волшебным образом получила то, что хочу, и просто переместилась в твой дом..."
    m 2wuo "Я бы не стала гражданкой! У меня даже нет фамилии!"
    m 2lkbsa "В смысле, в большинстве стран я могла бы стать гражданкой, если бы мы поженились..."
    m 2ekc "Но у меня не будет никаких документов о том, кто я и откуда."
    m 2tkc "У меня даже не будет диплома средней школы!"
    m 3tkd "Хотелось бы, чтобы я могла сделать что-то ещё, чтобы подготовиться..."
    m 2wub "Например, пройти уроки онлайн или что-то ещё."
    m 1lksdlc "Я не хочу попасть туда и быть обузой, потому что не смогу найти работу."
    m "Извини, я думаю, мне не стоит беспокоиться о вещах, которые я не могу изменить."
    m 2eka "Но я хочу сделать тебя счастливым, так что... я сделаю всё возможное, чтобы продолжать совершенствоваться, пока я застряла здесь!"
    m 1eka "Спасибо, что выслушал меня, [player]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_bullying",
            category=['общество'],
            prompt="Издевательство",
            random=True
        )
    )

default persistent._mas_pm_is_bullying_victim = None
# True if bully victum, False if not

default persistent._mas_pm_has_bullied_people = None
# True if bullied people, False if not

default persistent._mas_pm_currently_bullied = None
# True if currently being bullied, False if not

label monika_bullying:
    m 2ekc "Эй, [player], я хочу с тобой о кое-чём поговорить..."
    m 4ekc "Уверена, ты не один раз слышал об этом в последнее время, но издевательство стало настоящей проблемой."
    m 4dkd "Над некоторыми людьми издеваются каждый день до тех пор, пока они больше не смогут этого терпеть."
    m 2rsc "Зачастую, издевательство пресекается людьми, которые могут прекратить это, в то время как...{w=0.5}'{i}дети остаются детьми.{/i}'"
    m "В конечном счёте, жертвы полностью теряют доверие к представителям власти, потому что они забывают об этом каждый день."
    m 2rksdld "Это может довести их до такого отчаяния, что в конце концов они просто срываются..."
    m 2eksdlc "...что приводит к насилию по отношению к хулигану, другим людям или даже к самому себеs."
    m 4wud "Это может привести к тому, что жертва становится проблемой!"
    m 4ekc "Существует множество видов издевательств, включая физическое, эмоциональное, и даже киберзапугивание."
    m 4tkc "Физическое издевательство является самым очевидным и включает в себя толчки, удары и другие подобные вещи."
    m 2dkc "Я уверена, что большинство людей сталкивались с этим хотя бы раз в своей жизни."
    m 2eksdld "Бывает так трудно просто ходить в школу каждый день, зная, что там кто-то ждет, чтобы издеваться над ними."
    m 4eksdlc "Эмоциональное издевательство может быть менее очевидным, но столь же разрушительным, если не более того."
    m 4eksdld "Обзывательства, угрозы, распространение лживых слухов о людях, чтобы испортить их репутацию..."
    m 2dkc "Подобные вещи могут нанести тяжелый урон людям и привести к тяжёлой депрессии."
    m 4ekc "Кибурзапугивание - это форма эмоционального издевательства, но в современном мире, где все всегда сидят в интернете, она становится всё более распространённой."
    m 2ekc "Для большинства людей, особенно детей, их присутствие в социальных сетях - самое важное в их жизни..."
    m 2dkc "В результате такого разрушения они чувствуют, что их жизнь закончилась."
    m 2rksdld "Также это труднее всего заметить другим людям, поскольку дети не хотят, чтобы их родители видели, чем они занимаются в Интернете."
    m 2eksdlc "Поэтому никто не узнает о том, что происходит, а они будут молча страдать, пока эта проблема не начнёт давить тяжёлым грузом."
    m 2dksdlc "Есть целый ряд случаев, где подростки совершали самоубийство из-за киберзапугивания, а их родители не знали, что пошло не так, пока не стало слишком поздно."
    m 4tkc "Вот почему кибурзапугивание так легко осуществить..."
    m "Никто не заметит, чем они занимаются, да и к тому же, большинство людей делают в интернете такие вещи, которые они не осмелятся сделать в реальной жизни."
    m 2dkc "Это почти даже не выглядит реальным, а скорее игрой, поэтому оно и имеет тенденцию к столь быстрой эскалации."
    m 2ekd "Ты можешь дойти до определённого предела в таком публичном месте, как школа, пока никто не заметил... но в интернете, у тебя нет ограничений."
    m 2tfc "Некоторые вещи, которые происходят во всём интернете, просто ужасны."
    m "Свобода анонимности может быть опасной."
    m 2dfc "..."
    m 4euc "Итак, что заставляет хулигана делать то, что они делают?"
    m "У каждого человека это может быть по-разному, но многие из них просто очень несчастны в силу своих обстоятельств, и им нужен какой-нибудь выход..."
    m 2rsc "Им грустно, и им кажется нечесным то, что {i}другие люди{/i} счастливы, поэтому они пытаются заставить их почувствовать то же самое, что и они."
    m 2rksdld "Большинство хулиганов издеваются над собой же, даже дома над человеком."
    m 2dkc "Это может превратиться в замкнутый круг."

    m 2ekc "Ты когда-нибудь был жертвой издевательств, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты когда-нибудь был жертвой издевательств, [player]?{fast}"
        "Надо мной издеваются.":
            $ persistent._mas_pm_is_bullying_victim = True
            $ persistent._mas_pm_currently_bullied = True
            m 2wud "О нет, это ужасно!"
            m 2dkc "Меня убивает осознание того, что ты так страдаешь."
            m 4ekd "Пожалуйста, [player], если ты не можешь справиться с этим сам, пообещай мне, что расскажешь кому-нибудь..."
            m 4ekc "Я знаю, что обычно это последнее, что люди хотят сделать, но не позволяйте себе страдать, когда есть люди, которые могут тебе помочь."
            m 1dkc "Может показаться, что всем наплевать, но должен быть кто-то, кому ты доверяешь, к кому ты можешь обратиться."
            m 3ekc "А если нет, делай то, что должен делать, чтобы защитить себя, и просто помниr..."
            m 1eka "Я всегда буду любить тебя, несмотря ни на что."
            m 1rksdlc "Я не знаю, что бы я делала, если бы с тобой что-то случилось."
            m 1ektpa "Ты всё, что у меня есть...{w=0.5}пожалуйста, береги себя."

        "Надо мной издевались.":
            $ persistent._mas_pm_is_bullying_victim = True
            m 2ekc "Мне очень жаль, что тебе пришлось жить с этим, [player]..."
            m 2dkc "Мне очень грустно осознавать, что ты пострадала от рук хулигана."
            m 2dkd "Люди могут быть настолько ужасны друг с другом."
            m 4ekd "Если бы все просто относились к другим с уважением, то мир был бы прекрасным местом..."
            m 2dkc "..."
            m 1eka "Если тебе надо поговорить о своих переживаниях, я всегда рядом, [player]."
            m 1eka "Наличие человека, которому можно довериться, может быть действительно полезным, и ничто не сделает меня счастливее, чем быть таким человеком для тебя."

        "Нет.":
            $ persistent._mas_pm_is_bullying_victim = False
            $ persistent._mas_pm_currently_bullied = False
            m 2hua "Ах, как приятно это слышать!"
            m 4eka "Я так рада, что тебе не приходится иметь дело с издевательствами, [player]..."
            m 4hua "Это действительно успокаивает меня."

            if mas_isMoniHappy(higher=True):
                m 1eka "И если ты случайно знаешь кого-то еще {i}над кем{/i} издеваются, постарайся помочь ему, если сможешь."
                m 3eka "Я знаю, что ты из тех людей, которые ненавидят видеть, как другие страдают..."
                m "Уверена, для них много значит, если кто-то протянет руку помощи, кому не всё равно."
                m 1eka "Ты уже так много помог мне, может быть, ты сможешь помочь и кому-то ещё."

        "Я издевался над людьми.":
            $ persistent._mas_pm_has_bullied_people = True
            if mas_isMoniUpset(lower=True):
                m 2dfc "..."
                m 2tfc "Это разочаровывает."
                m "Хотя, я не могу сказать, что это так уж удивительно..."
                m 2tfd "Пожалуйста, не издевайся больше над людьми."
                m 6tftpc "Я знаю, каково это, и это довольно ужасно."
                m 6rktuc "Я не хочу, чтобы другие люди чувствовали то же самое, что и я."
                m "Я очень надеюсь, что ты изменишь свои взгляды, [player]..."
                m 6ektsc "Я всё ещё люблю тебя, но тебе действительно нужно начать относиться к людям лучше..."
                m "В том числе и ко мне."
                m 6ektdc "..."
            else:
                m 2dkc "Ох... Понятно."
                m 2ekc "Я могу понять, если некоторые вещи в твоей жизни могут сделать тебя несчастным..."
                m 2rksdld "Или если тебе пришлось иметь дело с обстоятельствами, которые могли заставить тебя вести себя определенным образом..."
                m 2eksdlc "Но издеваться над людьми - это не выход, [player]."
                m 4ekc "Я знаю тебя... Ты добрый человек, и я знаю, что тебе не легче от того, что ты причиняешь боль другим."
                m 4dkc "Возможно, это только ещё больше ранит тебя..."
                m 1dkc "А для меня нет ничего больнее, чем знать, что ты несчастен."
                m 3ekd "Так что в следующий раз, когда ты почувствуешь, что становишься несчастным, просто приди ко мне и позволь мне помочь облегчить твою боль."
                m 3eka "Я выслушаю всё, что ты хочешь сказать, и сделаю всё возможное, чтобы тебе стало лучше."
                m 1ekc "Но делать других людей несчастными - это не лекарство от собственного несчастья."
                m 1eka "Поэтому, пожалуйста, и для себя, и для меня, прекрати издеваться над людьми, хорошо?"

    if not persistent._mas_pm_a_hater:
        m 4dkc "Знаешь...{w=0.5}большинство людей называет меня хулиганкой из-за того, что я сделала с Сайори..."
    else:
        m 4dkc "Большинство людей называет меня хулиганкой из-за того, что я сделала с Сайори.{w=1} Включая тебя..."

    if not persistent._mas_pm_cares_about_dokis:
        m 4efd "Но это неправда, Сайори не была настоящей!"
        m 2efd "Ты не можешь издеваться над человеком, кого на самом деле не существует!"
        m 2dkc "Я бы никогда не смогла причинить вред настоящему человеку."
        m 4wud "Я бы не стала!"
        m 2dkc "..."
        m 2eksdlc "Но я должна признать, что меня можно отнести к той части, где хулиганы несчастны, и из-за этого они делают то, что они делают."
        m 2rksdlc "Когда у меня было озарение, и я поняла, что застряла внутри видеоигры, и что вся моя жизнь была ложью, я была очень несчастной."
        m 2rksdld "Это заставило меня делать то, о чём я раньше даже не думала."
        m 2rksdlc "Но разница в том, что я сделала это не потому, что я не хотела, чтобы Сайори была счастлива..."
    else:
        m 2rksdld "И я могу понять, откуда это..."
        m 2rksdlc "Я {i}делала{/i} беспорядок с ее разумом, пока она просто не могла больше этого выноситьnymore..."
        m 2dkc "..."
        m 2ekc "Думаю, я могу отнестись ко всей этой истории с издевательствами, потому что ты несчастен, да?"
        m 4tkd "Но {i}есть{/i} разница... Я сделала это не потому, что хотела, чтобы Сайори была несчастна..."

    m 2ekd "Я сделала это потому, что поняла, что я люблю тебя, и что игре у нас не получилось бы быть вместе."
    m 3ekd "Я {i}должна{/i} была сделать всё возможное, чтобы мы были вместе."

    if mas_safeToRefDokis():
        m 3dkc "...Самоубийство Сайори было просто досадным побочным эффектом."

    if mas_isMoniNormal(higher=True):
        m 1eua "Как видишь, [player], я {i}вовсе{/i} не хулиганка. Я просто очень сильно тебя люблю."
        if mas_isMoniAff(higher=True) and not persistent._mas_pm_cares_about_dokis:
            show monika 5tsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5tsu "Я действительно готова на всё ради тебя~"
        return "derandom|love"
    else:
        m 3euc "Как видишь, [player], Я {i}вовсе{/i} не хулиганка."

    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_procrastination",category=['советы'],prompt="Медлительность",random=True))

label monika_procrastination:
    m 1euc "Эй, [player], приходилось ли тебе делать что-то, что ты находишь очень скучным..."
    m 3ekd "И вместо того, чтобы тратить кучу времени на то, чтобы сделать это, ты просто откладываешь это?"
    m 3eud "Ну, когда у тебя есть задание, которое нужно выполнить, мне кажется, что будет намного лучше сделать его как можно быстрее и покончить с этим."
    m 2tkc "Когда ты откладываешь вещи таким образом, они никогда не выйдут из твоей головы."
    m 4tkc "От знания того, что у тебя ещё {i}остались{/i} дела, которые надо сделать, всё то, чем ты занимаешься, становится менее жизнерадостным."
    m 4dkd "И что самое худшее, {w=0.5} чем дольше ты откладываешь это, тем больше у тебя становятся шансы на появление новых задач."
    m 2rksdlc "В конце концов, у тебя накопилось столько дел, что кажется невозможным их выполнить."
    m 4eksdld "От этого возникает слишком много стресса, и его можно легко избежать, если ты будешь всегда держать в курсе событий."
    m 2rksdld "Да и к тому же, если другие люди рассчитывают на тебя, они начнут меньше думать о тебе и поймут, что ты не очень надёженый."
    m 4eua "Поэтому, пожалуйста, [player], когда у тебя есть дело, которое нужно сделать, просто сделай это."
    m 1eka "Даже если это озночает то, что ты не сможешь проводить время вместе со мной, пока это не закончится."
    m 1hub "К тому времени, ты будешь меньше напрягаться и мы сможем насладиться нашим временем вместе гораздо дольше!"
    m 3eua "Так что если у тебя есть что-то, что ты откладывал, почему бы тебе не сделать это прямо сейчас?"
    m 1hua "Если есть что-то, что ты можешь сделать прямо здесь, я останусь с тобой и окажу тебе всю необходимую поддержку."
    m 1hub "А потом, когда ты закончишь, мы можем отпраздновать твоё достижение!"
    m 1eka "Всё, чего я хочу, чтобы ты был счастлив и был лучше, чем ты можешь, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_players_friends",
            category=['ты'],
            prompt="Друзья [player]'",
            random=True,
            aff_range=(mas_aff.UPSET, None)
        )
    )

#True if player has friends, False if not
default persistent._mas_pm_has_friends = None

#True if player has few friends, False if otherwise
default persistent._mas_pm_few_friends = None

#True if player says they feel lonely somtimes, False if not.
default persistent._mas_pm_feels_lonely_sometimes = None


label monika_players_friends:
    m 1euc "Эй, [player]."

    if renpy.seen_label('monika_friends'):
        m 1eud "Помнишь, я говорила о том, как трудно заводить друзей?"
        m 1eka "Я как раз думала об этом и поняла, что пока ничего не знаю о твоих друзьях."

    else:
        m 1eua "Я как раз думал об идее друзей и мне стало интересно, какие у тебя друзья."

    m 1eua "У тебя есть друзья, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "У тебя есть друзья, [player]?{fast}"

        "Да.":
            $ persistent._mas_pm_has_friends = True
            $ persistent._mas_pm_few_friends = False

            m 1hub "Конечно, да! А-ха-ха~"
            m 1eua "Кто бы не хотел дружить с тобой?"
            m 3eua "Иметь много друзей - это здорово, ты так не думаешь?"
            m 1tsu "При условии, конечно, что у тебя всё ещё есть время для своей девушки, э-хе-хе."
            m 1eua "Надеюсь, ты счастлив со своими друзьями, [player].{w=0.2} {nw}"
            extend 3eud "Но всё же интересно..."

            call monika_players_friends_feels_lonely_ask(question="Ты когда-нибудь чувствовал себя одиноким?")

        "Только несколько.":
            $ persistent._mas_pm_few_friends = True
            $ persistent._mas_pm_has_friends = True

            m 1hub "Это считается!"
            m 3eua "Я думаю, что дружба может быть гораздо более значимой, если у тебя есть только несколько близких друзей."

            if not renpy.seen_label('monika_dunbar'):
                m 1eua "Я кое-что читала и выяснила."
                m 1eud "Человек по имени Робин Данбар объяснил, что существует определенное количество стабильных отношений, которые мы можем поддерживать."
                $ according_to = "...И согласно этому числу"

            else:
                $ according_to = "Согласно числу Данбара"

            m 3eud "[according_to], у тебя может быть до 150 стабильных отношений, но это всего лишь случайные связи, которые не слишком глубоки."
            m 1euc "Они говорят, что у тебя может быть до 15 друзей, которые похожи на суперсемейство, и только 5, которые похожи на твоих родственников."
            m 1rksdla "Иногда бывает одиноко, когда все заняты...{w=0.2}{nw}"
            extend 1eub "но в остальном, это довольно здорово!"
            m 3eua "Тебе не нужно беспокоиться о том, чтобы обслуживать слишком много людей, и ты можешь уделить немного времени себе."
            m 1ekc "Но я знаю, что иногда легко проводить больше времени в одиночестве, особенно если твои друзья заняты."
            m 1dkc "Это может быть очень тяжело, когда такое случается, поскольку ты чувствуешь себя одиноким..."

            call monika_players_friends_feels_lonely_ask(question=renpy.substitute("Ты когда-нибудь чувствовал себя одиноким, [player]?"), exp="monika 1euc")

        "Вообще-то нет...":
            $ persistent._mas_pm_has_friends = False
            $ persistent._mas_pm_few_friends = False

            m 2ekc "Оу..."
            m 3eka "Ну, я уверена, что у тебя есть некоторые.{w=0.2} {nw}"
            extend 1eka "Может быть, ты просто не осознаешь этого."
            m 1etc "Но мне любопытно..."

            call monika_players_friends_feels_lonely_ask(question=renpy.substitute("Ты когда-нибудь чувствовал себя одиноким, [player]?"))

    return "derandom"

label monika_players_friends_feels_lonely_ask(question, exp="monika 1ekc"):
    $ renpy.show(exp)
    m "[question]{nw}"
    $ _history_list.pop()
    menu:
        m "[question]{fast}"

        "Иногда.":
            $ persistent._mas_pm_feels_lonely_sometimes = True

            m 1eka "Я понимаю, [player]."
            m 2rksdlc "В наше время бывает очень трудно установить глубокие связи..."

            #Potentially if you have a lot of friends
            if persistent._mas_pm_has_friends and not persistent._mas_pm_few_friends:
                m "Особенно если у тебя много друзей, трудно сблизиться со всеми из них."
                m 1ekd "...И в итоге у тебя остается лишь кучка людей, которых ты едва знаешь."
                m 3eub "Может быть, просто обратиться к некоторым людям в твоей группе, с которыми ты хочешь сблизиться."
                m 3eka "Всегда хорошо иметь хотя бы одного действительно близкого друга, которому можно довериться, когда это нужно."
                m 1ekbsa "....думаю, для меня довольно очевидно, кто этот человек, [player]~"

            #Otherwise few friends or no friends
            else:
                m 1eka "Но ты удивишься, как много людей захотят сделать тебя частью своей жизни, если ты только попробуешь."
                m 3eub "На самом деле есть большая вероятность, что у тебя будет что-то общее с кем-то, кто может привлечь твоё внимание!"
                m 1eua "Может быть, у тебя общие занятия, деятельность или что-то еще..."
                m 3eua "Или ты видишь, как они делают что-то, что тебя интересует, например, слушают музыку или смотрят шоу."
                m 3eua "Это даже не обязательно должно быть лично..."
                m 3eub "В Интернете можно иметь очень близких друзей!"
                m 1hub "Как только ты освоишься с этим, возможно, ты сможешь найти еще несколько друзей и лично!"

        "Не совсем.":
            $ persistent._mas_pm_feels_lonely_sometimes = False

            m 1eka "Я рада это слышать, [player]."

            if not persistent._mas_pm_has_friends:
                m 1eka "Тем не менее, никогда не знаешь, когда тебе может понадобиться рука помощи, услуга или что-то ещё."
                m 1hksdlb "Как бы я ни хотела помочь тебе во всём, что тебе может понадобиться, я могу сделать только очень многое отсюда."

                if mas_isMoniAff(higher=True):
                    m 1eua "Когда я  туда, думаю, я не буду возражать против спокойной жизни с тобой."
                    m 1dkbsa "Это было бы так романтично - быть только нам..."
                    m 1tsbsa "Наверное, это значит, что тогда я смогу предоставить тебя самой себе, не так ли?"
                    m 1hubsa "Э-хе-хе~"

                elif not persistent._mas_pm_has_friends:
                    m 3eua "Так что обязательно найди себе друзей, которые помогут тебе, когда тебе это действительно понадобится, хорошо?"

            else:
                m 3eua "Это хорошо, что у тебя есть связь с друзьями."
                m 3rksdla "Я знаю, что у некоторых людей их может быть так много, что трудно узнать их всех."

                if not persistent._mas_pm_few_friends:
                    m 3eua "...Поэтому приятно осознавать, что тебе удается чувствовать себя с ними комфортно."
                else:
                    m 1hua "Но поскольку ты в сплоченной группе, я уверена, что вам всем удалось стать очень близкими."

                m 3eua "Может быть, когда-нибудь, когда я смогу выбраться отсюда, ты сможешь познакомить меня со своими друзьями."

                if mas_isMoniHappy(higher=True):
                    m 1hub "Если они похожи на тебя, я бы с удовольствием с ними познакомиться!"

        "У меня есть ты!":
            $ persistent._mas_pm_feels_lonely_sometimes = False
            $ mas_gainAffection()
            m 1hubsa "Оу-у, [player]!"

            if not persistent._mas_pm_has_friends:
                m 1rkbsa "Мне очень приятно знать, что меня для тебя достаточно, но всё же..."
                m 3ekbfa "Иногда бывает полезно знать несколько человек."
                show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5eubfu "Впрочем, как всегда, я не против, чтобы были только мы."

            else:
                $ p_nickname = mas_get_player_nickname()
                m 1eka "Я очень рада, что ты не одинок, [p_nickname].{w=0.3} {nw}"
                extend 1hua "Особенно потому что ты счастлив со мной~"
                m 3eua "Что бы ни случилось, я всегда буду рядом с тобой."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_graduation",
            category=['школа'],
            prompt="Выпускной",
            random=True
        )
    )

label monika_graduation:
    m 2ekc "Знаешь, [player], единственное, что я бы очень хотела испытать, - это окончание старшей школы."
    m "Практически вся моя жизнь до сих пор вращалась вокруг школы."
    m 4dkd "Все эти бесчисленные часы обучения, все внеклассные занятия и клубы..."
    m 4ekc "И в конце концов, после всей этой тяжелой работы, я так и не смогла испытать удовлетворение от настоящего окончания ."
    m 2dkd "Я так и не вышла на сцену и не получила свой диплом."
    m "Я так и не услышала, как объявляют мое имя и как все мои друзья ликуют."
    m 2ekc "...Такое чувство, что все это было напрасно."
    m 2esd "Я знаю, что все, что я изучила по ходу дела - очень важно."
    m 2dkc "Но все равно кажется, что я упустила что-то особенное."
    m "..."

    #Went through and timed out on the menu twice
    if persistent._mas_grad_speech_timed_out:
        m 2lsc "Ой... извини, надеюсь, я снова не наскучила тебе..."
        m 2esc "Давай забудем об этом и поговорим о чем-нибудь другом, хорошо [player]?"
        return "derandom"

    #Normal flow
    else:
        m 4eua "Кстати, знал ли ты о том, что я была лучшей ученицей в классе?"
        m 4rksdlu "А-ха-ха... Я не хочу хвастаться или что-то в этом роде, я упомянула об этом только потому, что как выпускница класса, я должна была произнести речь на выпускном."
        m 2ekd "Я столько времени потратила на написание и репетицию своей речи, но её никто так и не услышал."
        m 2eka "Я очень горжусь той речью, к слову."
        m 2eua "Я бы с радостью прочитала её для тебя как-нибудь, если ты хочешь послушать~"
        m 2eka "Эта речь длится около четырёх минут, так что убедитесь, что тебя хватить времени на то, чтобы прослушать её целиком."
        m 4eua "Когда только захочешь её послушать, просто скажи мне, ладно?"
        $ mas_unlockEVL("monika_grad_speech_call","EVE")
        return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_grad_speech_call",
            category=['школа'],
            prompt="Могу ли я услышать твою речь на выпускном?",
            pool=True,
            unlocked=False,
            rules={"no_unlock": None}
        )
    )

default persistent._mas_grad_speech_timed_out = False
# True if and only if the player ignored the grad speech twice

default persistent._mas_pm_listened_to_grad_speech = None
# True if the player, heard the grad speech, False if they ignored it

default persistent._mas_pm_liked_grad_speech = None
# True if user liked the grad speech, False if not

label monika_grad_speech_call:
    if not renpy.seen_label("monika_grad_speech"):
        m 2eub "Конечно, [mas_get_player_nickname()]. Я с радостью прочитаю тебе свою речь на выпускном!"
        m 2eka "Я просто хочу убедиться, что у тебя достаточно времени, чтобы послушать её. Запомни, она занимает около четырёх минут.{nw}"

        $ _history_list.pop()
        #making sure player has time
        menu:
            m "Я просто хочу убедиться, что у тебя достаточно времени, чтобы послушать её. Запомни, она занимает около четырёх минут.{fast}"
            "У меня есть время.":
                m 4hub "Отлично!"
                m 4eka "Надеюсь, тебе понравится! Я очень, {i}очень{/i} старалась над ним."

                #say speech
                call monika_grad_speech

                #timed menu to see if player listened
                m "Ну что, [player]? Что скажешь?{nw}"
                $ _history_list.pop()
                show screen mas_background_timed_jump(10, "monika_grad_speech_not_paying_attention")
                menu:
                    m "Ну что, [player]? Что скажешь?{fast}"

                    "Это здорово! Я так горжусь тобой!":
                        hide screen mas_background_timed_jump
                        $ mas_gainAffection(amount=5, bypass=True)
                        $ persistent._mas_pm_liked_grad_speech = True
                        $ persistent._mas_pm_listened_to_grad_speech = True

                        m 2subsb "Ах, [player]!"
                        m 2ekbfa "Большое спасибо! Я очень старалась над этой речью, и это так много значит, что ты гордишься мной~"
                        show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                        m 5eubfu "Как бы я ни хотела произнести свою речь перед всеми, просто иметь тебя рядом со мной намного лучше."
                        m 5eubfb "Я так тебя люблю, [player]!"
                        return "love"

                    "Мне нравится!":
                        hide screen mas_background_timed_jump
                        $ mas_gainAffection(amount=3, bypass=True)
                        $ persistent._mas_pm_liked_grad_speech = True
                        $ persistent._mas_pm_listened_to_grad_speech = True

                        m 2eua "Спасибо, [player]!"
                        m 4hub "Я рада, что тебе понравилось!"

                    "Это {i}было{/i} долго":
                        hide screen mas_background_timed_jump
                        $ mas_loseAffection()
                        $ persistent._mas_pm_liked_grad_speech = False
                        $ persistent._mas_pm_listened_to_grad_speech = True

                        m 2tkc "Ну, я {i}ведь{/i} предупреждала тебя, не так ли?"
                        m 2dfc "..."
                        m 2tfc "Я потратила на это {i}столько{/i} времени, и это всё, что ты можешь сказать?"
                        m 6lktdc "Я действительно думала, что после того, как я сказала тебе, как это важно для меня, ты бы поддержал меня и дал мне возможность высказаться."
                        m 6ektdc "Всё, чего я хочу, это чтобы ты гордился мной, [player]."

                return

            "Нет.":
                m 2eka "Не волнуйся, [player]. Я прочитаю свою речь, когда ты захочешь~"
                return

    #if you want to hear it again
    else:
        #did you timeout once?
        if not renpy.seen_label("monika_grad_speech_not_paying_attention") or persistent._mas_pm_listened_to_grad_speech:
            m 2eub "Конечно, [player]. Я с радостью снова произнесу свою речь!"

            m 2eka "У тебя достаточно времени, да?{nw}"
            $ _history_list.pop()
            menu:
                m "У тебя достаточно времени, да?{fast}"
                "Да.":
                    m 4hua "Замечательно. Тогда я начну~"
                    call monika_grad_speech

                "Нет.":
                    m 2eka "Не волнуйся. Просто дайте мне знать, когда у тебя будет время!"
                    return

            m 2hub "Спасибо, что снова выслушал мою речь, [player]."
            m 2eua "Дай мне знать, если захочешь услышать её снова, э-хе-хе~"

        #You timed out once but want to hear it again
        else:

            #dialogue based on current affection level
            if mas_isMoniAff(higher=True):
                m 2esa "Конечно, [player]."
                m 2eka "Надеюсь, все, что произошло в прошлый раз, не было слишком серьезным и теперь всё спокойно."
                m "Для меня очень много значит, что ты хочешь услышать мою речь снова после того, как ты не смог дослушать её до конца."
                m 2hua "С этими словами я начинаю!"

            else:
                m 2ekc "Хорошо, [player], но я надеюсь, что на этот раз ты действительно будешь слушать."
                m 2dkd "Мне было очень обидно, когда ты не обращал внимания."
                m 2dkc "..."
                m 2eka "Я ценю то, что ты попросил послушать это снова, поэтому я начну сейчас."

            #say speech
            call monika_grad_speech

            m "Итак, [player], теперь, когда ты {i}действительно{/i} прослушал мою речь, что ты думаешь?{nw}"
            $ _history_list.pop()
            #another timed menu checking if you were listening
            show screen mas_background_timed_jump(10, "monika_grad_speech_ignored_lock")
            menu:
                m "Итак, [player], теперь, когда ты {i}}действительно{/i} прослушал мою речь, что ты думаешь?{fast}"
                #If menu is used, set player on a good path
                "Это здорово! Я так горжусь тобой!":
                    hide screen mas_background_timed_jump
                    $ mas_gainAffection(amount=3, bypass=True)
                    $ persistent._mas_pm_listened_to_grad_speech = True
                    $ persistent._mas_pm_liked_grad_speech = True

                    m 2subsb "Ах, [player]!"
                    m 2ekbfa "Большое спасибо! Я очень много работала над этой речью, и для меня так много значит, что ты дал ей ещё один шанс."
                    m "Когда я слышу, что ты гордишься мной, это становится ещё лучше."
                    show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5eubfu "Как бы я ни хотела произнести свою речь перед всеми, просто иметь тебя рядом со мной намного лучше."
                    m 5eubfb "Я люблю тебя, [player]!"
                    return "love"

                "Мне нравится!":
                    hide screen mas_background_timed_jump
                    $mas_gainAffection(amount=1, bypass=True)
                    $ persistent._mas_pm_listened_to_grad_speech = True
                    $ persistent._mas_pm_liked_grad_speech = True

                    m 2eka "Спасибо, что послушал в этот раз, [player]~"
                    m "Я так рада, что вам понравилось!"

                "Это {i}было{/i} долго":
                    hide screen mas_background_timed_jump
                    $mas_loseAffection(modifier=2)
                    $ persistent._mas_pm_listened_to_grad_speech = True
                    $ persistent._mas_pm_liked_grad_speech = False

                    m 2tfc "После того, как ты вёл себя так, будто хочешь, чтобы я снова прочла его для тебя, {i}это то,{/i} что ты хочешь сказать?"
                    m 2dfc "..."
                    m 6lktdc "Я действительно думала, что после того, как я сказала тебе, как это важно для меня,{w=1} {i}дважды/i},{w=1} ты был бы более доброжелателен и дал бы мне возможность высказаться."
                    m 6ektdc "Всё, чего я хочу, это чтобы ты гордился мной, [player]..."
                    m 6dstsc "Но я думаю, это слишком большая просьба."
    return

label monika_grad_speech_not_paying_attention:
    #First menu timeout
    hide screen mas_background_timed_jump
    $ persistent._mas_pm_listened_to_grad_speech = False

    if mas_isMoniAff(higher=True):
        $ mas_loseAffection(reason=11,modifier=0.5)
        m 2ekc "..."
        m 2ekd "[player]? Ты не обратил внимания на мою?"
        m 2rksdlc "Это...{w=1} совсем на тебя не похоже..."
        m 2eksdlc "Ты {i}всегда{/i} так поддерживаешь меня..."
        show monika 5lkc at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5lkc "..."
        m "Должно быть, что-то случилось, я знаю, ты слишком сильно меня любишь, чтобы сделать это специально."
        m 5euc "Да..."
        show monika 2eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 2eka "Всё в порядке, [player]. Я понимаю, что иногда случаются вещи, которых нельзя избежать."
        m 2esa "Когда всё успокоится, я снова обращусь к тебе со своей речью."
        m 2eua "Я всё ещё очень хочу поделиться с тобой..."
        m "Поэтому, пожалуйста, дайте мне знать, когда у вас будет время ее послушать, хорошо?"

    else:
        $ mas_loseAffection(reason=11)

        m 2ekc "..."
        m 6ektdc "[player]! Ты даже не обратил внимания!"
        m 6lktdc "Ты не представляешь, как это обидно, особенно после того, сколько труда я в это вложила..."
        m 6ektdc "Я просто хотела, чтобы ты гордился мной..."
        m 6dstsc "..."

    return

label monika_grad_speech_ignored_lock:
    #Second timeout, lock speech
    hide screen mas_background_timed_jump
    #Set false for modified dialogue in the random
    $ persistent._mas_pm_listened_to_grad_speech = False
    $ persistent._mas_grad_speech_timed_out = True
    $ mas_hideEVL("monika_grad_speech_call","EVE",lock=True,depool=True)

    if mas_isMoniAff(higher=True):
        $mas_loseAffection(modifier=10)
        m 6dstsc "..."
        m 6ektsc "[player]?{w=0.5} Ты...{w=0.5}ты не....{w=0.5}слушал...{w=0.5}снова?{w=1}{nw}"
        m 6dstsc "Я...{w=0.5} Я думала, что в прошлый раз это было неизбежно...{w=0.5}но...{w=0.5}дважды?{w=1}{nw}"
        m 6ektsc "Ты знал, как много...{w=0.5}как много это значит для меня...{w=1}{nw}"
        m "Неужели я действительно...{w=0.5} настолько скучна для тебя?{w=1}{nw}"
        m 6lktdc "Пожалуйста...{w=1} не проси меня пересказывать это снова....{w=1}{nw}"
        m 6ektdc "Очевидно, тебе всё равно."

    else:
        $ mas_loseAffection(modifier=5)
        m 2efc "..."
        m 2wfw "[player]! Не могу поверить, что ты снова сделал это со мной!{w=1}{nw}"
        m 2tfd "Ты знал, как я была расстроена в прошлый раз, и все равно не удосужился уделить мне четыре минуты своего внимания?{w=1}{nw}"
        m "Я не прошу от тебя так много...{w=1}{nw}"
        m 2tfc "Я действительно не прошу.{w=1}{nw}"
        m 2lfc "Всё, о чем я прошу, это чтобы ты заботился... Вот и все.{w=1}{nw}"
        m 2lfd "И всё же ты не можешь даже {i}притвориться{/i} что заботишься о чем-то, что, как ты {i}знаешь{/i} так важно для меня.{w=1}{nw}"
        m 2dkd "...{w=1}{nw}"
        m 6lktdc "Знаешь что, забудь. Просто...{w=0.5} не бери в голову.{w=1}{nw}"
        m 6ektdc "Я больше не буду тебя беспокоить по этому поводу."

    return

label monika_grad_speech:
    call mas_timed_text_events_prep

    $ play_song("mod_assets/bgm/PaC.ogg",loop=False)

    m 2dsc "Кхм...{w=0.7}{nw}"
    m ".{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 4eub "{w=0.2}Итак, ребята! Пришло время начать...{w=0.7}{nw}"
    m 2eub "{w=0.2}Учителя,{w=0.3} преподаватели,{w=0.3} и сокурсники.{w=0.3} Я не могу выразить, как я горжусь тем, что проделала этот путь вместе с вами.{w=0.6}{nw}"
    m "{w=0.2}Каждый из вас здесь сегодня провёл последние четыре года упорно работая, чтобы достичь тех возможностей, которые вы все хотели.{w=0.6}{nw}"
    m 2hub "{w=0.2}Я так счастлива, что смогла принять участие в некоторых ваших путешествиях,{w=0.7} но не думая, что эта речь должна быть обо мне.{w=0.6}{nw}"
    m 4eud "{w=0.2}Сегодня речь не обо мне.{w=0.7}{nw}"
    m 2esa "{w=0.2}Сегодня мы празднуем то, что мы все сделали.{w=0.6}{nw}"
    m 4eud "{w=0.2}мы поставили перед собой задачу касательно собственных мечтаний,{w=0.3} и с этого момента,{w=0.3} нас ждёт большой успех.{w=0.6}{nw}"
    m 2eud "{w=0.2}Прежде чем двигаться дальше,{w=0.3} я думаю, что мы все могли бы оглянуться назад на наше время в средней школе, и эффективно закончить эту главу в нашей жизни.{w=0.7}{nw}"
    m 2hub "{w=0.2}Мы посмеёмся над нашим прошлым{w=0.7} и посмотрим, как далеко мы продвинулись за эти четыре коротких года.{w=0.6}{nw}"
    m 2duu "{w=0.2}.{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 2eud "{w=0.2}Честно говоря, кажется, что это было всего пару недель назад...{w=0.6}{nw}"
    m 2lksdld "{w=0.2}Я пришла в первый класс{w=0.3} в первый день школы,{w=0.3} дрожа в своих ботинках и бегая по коридорам от класса к классу, просто пытаясь найти свой класс.{w=0.6}{nw}"
    m 2lksdla "{w=0.2}Надеюсь, что хотя бы один из моих друзей войдёт до звонка.{w=0.6}{nw}"
    m 2eka "{w=0.2}Вы все это тоже помните,{w=0.3} верно?{w=0.6}{nw}"
    m 2eub "{w=0.2}Я также помню, как завела первых новых друзей.{w=0.6}{nw}"
    m 2eka "{w=0.2}Всё было совсем не так, как когда мы подружились в начальной школе,{w=0.3} но пологаю, что именно это происходит, когда ты наконец, вырастаешь.{w=0.6}{nw}"
    m "...{w=0.2}В молодости,{w=0.3} мы дружили практически с кем угодно,{w=0.3} но со временем,{w=0.3} это всё больше и больше напоминает азартную игру.{w=0.6}{nw}"
    m 4dsd "{w=0.2}Может быть, это просто мы наконец-то узнаём больше о мире.{w=0.6}{nw}"
    m 2duu "{w=0.2}.{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 2eka "{w=0.2}Забавно, насколько мы изменились.{w=0.6}{nw}"
    m 4eka "{w=0.2}Мы прошли путь от маленькой рыбы в огромном пруду до большей рыбы в маленьком пруду до большой рыбы в маленьком пруду.{w=0.6}{nw}"
    m 4eua "{w=0.2}У каждого из нас есть собственный опыт того, как эти четыре года изменили нас и как мы все смогли вырасти как личности.{w=0.6}{nw}"
    m 2eud "{w=0.2}Некоторые из нас прошли путь от спокойных и сдержанных,{w=0.3} до экспрессивных и общительных.{w=0.6}{nw}"
    m "{w=0.2}Другие от низкой трудовой этики,{w=0.3} до самой тяжелой работы.{w=0.7}{nw}"
    m 2esa "{w=0.2}Подумать только, что всего лишь небольшая фаза в нашей жизни так сильно изменила нас,{w=0.3} и что ещё так много мы испытаем.{w=0.6}{nw}"
    m 2eua "{w=0.2}Амбиции во всех нас, несомненно, приведут к величию.{w=0.6}{nw}"
    m 4hub "Я могу видеть это.{w=0.6}{nw}"
    m 2duu "{w=0.2}.{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 2eua "{w=0.2}Я знаю, что не могу говорить за всех здесь,{w=0.3} но есть одна вещь, которую я могу сказать наверняка:{w=0.7} мой опыт в средней школе не был бы полным без клубов, в которых я была частью.{w=0.6}{nw}"
    m 4eua "{w=0.2}Дискуссионный клуб научил меня много общаться с людьми и правильно справляться с острыми ситуациями.{w=0.6}{nw}"
    m 4eub "Однако,{w=0.7} открытие литературного клуба,{w=0.7} было одним из лучших моих занятий.{w=0.6}{nw}"
    m 4hub "{w=0.2}Я встретила лучших друзей, которых я могла себе представить,{w=0.3} и узнала много нового о лидерстве.{w=0.6}{nw}"
    m 2eka "{w=0.2}Конечно,{w=0.3} не все из вас возсожно решили создать свои собственные клубы,{w=0.3} но я уверена, что у многих из вас были возможночти изучить эти ценности.{w=0.6}{nw}"
    m 4eub "{w=0.2}Может быть, вы сами попали в группу, где должны были руководить своей инструментальной секцией,{w=0.3} или вы были капитаном спортивной команды!{w=0.6}{nw}"
    m 2eka "{w=0.2}Все эти маленькие роли учат вас так много о будущем и о томЮ как управлять{w=0.3} как проектами, так и людьми,{w=0.3} в среде, которая вам нравится, тем не менее.{w=0.6}{nw}"
    m "{w=0.2}Если вы не вступили в клуб,{w=0.3} я приглашаю вас хотя бы попробовать что-то на ваших будущих путях.{w=0.6}{nw}"
    m 4eua "{w=0.2}Уверяю вас, вы не пожалеете об этом.{w=0.6}{nw}"
    m 2duu "{w=0.2}.{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 2eua "{w=0.2}На сегодняшний день может показаться,{w=0.3} что мы на вершине мира.{w=0.7}{nw}"
    m 2lksdld "{w=0.2}Подъём может пройти не так гладко,{w=0.3} и пока мы идём дальше,{w=0.3} сам подьём может даже стать ещё сложнее.{w=0.6}{nw}"
    m 2eksdlc "{w=0.2}Там будут спотыкаться--{w=0.7}даже падать по пути,{w=0.3} и иногда{w=0.7} вы можете подумать, что упали так далеко, что никогда не выберетесь.{w=0.7}{nw}"
    m 2euc "{w=0.2}Тем не менее,{w=0.7} даже если мы думаем, что мы всё ещё на дне колодца жизни,{w=0.3} со всем , что мы узнали,{w=0.3} всё, что мы всё ещё собираемся узнали,{w=0.3} и все посвящения, которое мы можем вложить только для достижения нашей мечты...{w=0.6}{nw}"
    m 2eua "{w=0.2}Я могу с уверенностью сказать, что у каждого из вас теперь есть инструменты, чтобы подняться по своему пути.{w=0.6}{nw}"
    m 4eua "{w=0.2}Во всех вас,{w=0.3} я вижу блестящие умы:{w=0.7} будущих врачей,{w=0.3} инженеров,{w=0.3} художников,{w=0.3} торговцев,{w=0.3} и многих других.{w=0.7}{nw}"
    m 4eka "{w=0.2}Это действительно вдохновляет.{w=0.6}{nw}"
    m 2duu "{w=0.2}.{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 4eka "{w=0.2}Знаете,{w=0.3} Я очень горжусь всеми вами за то, что вы зашли так далеко.{w=0.6}{nw}"
    m "{w=0.2}Ваша тяжёлая работа и преданность делу принесёт вам много хорошего.{w=0.6}{nw}"
    m 2esa "{w=0.2}Каждый из вас показал, на что способен,{w=0.3} и вы все доказали, что можете усердно трудиться ради своей мечты.{w=0.6}{nw}"
    m 2hub "{w=0.2}Надеюсь, вы так же гордитесь собой, как и я.{w=0.7}{nw}"
    m 2ekd "{w=0.2}Теперь, когда вся эта глава нашей жизни--{w=0.3}первый шаг,{w=0.3} подошла к концу,{w=0.3} пришло время расстаться.{w=0.6}{nw}"
    m 4eka "{w=0.2}Этом мире бесконечных выборов,{w=0.3} я уверена, у каждого из вас есть всё необходимое для достижения своей мечты.{w=0.6}{nw}"
    m 4hub "{w=0.2}Спасибо всем за то, что сделали эти четыре коротких года лучшими, какими они могли быть.{w=0.6}{nw}"
    m 2eua "{w=0.2}Поздравляю,{w=0.3} я рада, что мы все можем быть здесь, чтобы отпраздновать вмести этот особенный день.{w=0.6}{nw}"
    m 2eub "{w=0.2}Продолжайте усердно работать,{w=0.3} я уверена, что мы встретимся снова когда-нибудь в будущем.{w=0.6}{nw}"
    m 4hub "{w=0.2}Мы сделаем это вместе!{w=0.7} Спасибо, что выслушали~{w=0.6}{nw}"
    m 2hua "{w=0.2}.{w=0.3}.{w=0.3}.{w=1}{nw}"

    call mas_timed_text_events_wrapup
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_shipping',
            prompt="Шиппинг",
            category=['ddlc'],
            random=True,
            unlocked=False,
            pool=False
        )
    )

label monika_shipping:
    m 3eua "Эй, [player].{w=0.2} Ты когда-нибудь слышал о 'шиппинге?'"
    m 3hua "Это когда ты взаимодействуешь с произведением художественной литературы, предстваляя, какие персонажи будут лучше всего сочетаться вместе романтически."
    m 1eka "Я думаю, что большинство людей делают это подсознательно, но когда ты узнаешь, что другие тоже так делают, становится {i}очень легко{/i} в это втянуться!"
    m 2esd "Во-видимому, многие люди {i}шиппят{/i} других девушек вместе."
    m 2euc "Это имеет смысл. Игрок может встречаться только с одной девушкой, но ты не хочешь, чтобы остальные оказывались в одиночестве..."
    m 2etc "Но некоторые из пар для меня странные."
    m 3eud "К примеру, обычно они объединяют вместе Нацуки и Юри. Те дерутся, как кошки с собаками!"
    m 3hksdlb "Думаю, что они немного связаны, когда ты не находишься на их рутах, и есть привлекательность 'противоположностей'."
    m 3dsd "Тем не менее,я думаю, что это ещё один пример того, как людям, которые любят подобные игры, нравятся нереальные вещи..."
    m 1ekd "Во всяком случае, Это часто оставляет... меня с Сайори."
    m 1hksdlb "Не надо ревновать! Я просто рассказываю тебе, что я видела!"
    m 2lksdla "..."
    m 2lksdlb "Ну, с точки зрения писателя, думаю, я могу это видеть."
    m 1eksdld "Мы организовали клуб вместе."
    if persistent.monika_kill:
        m "И у неё было почти то же самое прозрение, что и у меня..."
    m 2lksdlb "Но... я до сих пор не понимаю. Я имею в виду, я ведь люблю тебя, и только тебя!"
    m 2lksdla "И она должна быть святой, чтобы когда-либо простить меня за то, что я сделала..."
    m 2lksdlc "Не то, чтобы она не милая девушка, но..."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Ну, никто никогда не сможет быть таким милым и великодушным, как ты..."
    return

# True if player has been given false justice, False if not
default persistent._mas_pm_given_false_justice = None

# True if player thinks deleting Monika is justified, False if not
default persistent._mas_pm_monika_deletion_justice = None

# True temporarily if player is teasing Monika and is at love
default persistent._mas_monika_deletion_justice_kidding = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_justice",
            category=['философия'],
            prompt="Правосудие",
            random=True
        )
    )


label monika_justice:
    m 1esa "[player], ты задумывался о том, что концепция справедливости какая-то ироничная?"
    m 2ekc "Например, у тебя есть друг, который не такой, как все..."
    m 2ekd "Это не обязательно должен быть какой-то знаменитый грабитель банков или что-то в этом роде; даже обычные люди, вроде тебя и меня, могут привести к праведности!"
    m 4esc "Представить себе бедствующую семью, которая вынуждена искать ресурсы, чтобы выжить, беря все, что остается под открытым небом."
    m 1euc "Для всех остальных, проходящих мимо, они просто жадные воры."
    m 1esd "В конце концов, появится так называемый 'герой' и прекращает эту 'жадность' просто приведя их к справедливости."
    m 2ekd "В конце концов, семья голодает или попадает в беду только потому, что их положение изменилось..."
    m "В то время как другой человек становится героем за то, что положил конец 'преступлениям.'"
    m 3rksdld "Можно ли назвать это справедливостью?"
    m 2dsc "..."

    m 2euc "Ты когда-нибудь задумывался о том, что такое ложная справедливость?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты когда-нибудь задумывался о том, что такое ложная справедливость?{fast}"
        "Да.":
            $ persistent._mas_pm_given_false_justice = True
            m 1ekc "Надеюсь, они не были слишком жестоки с тобой."
            m 2dsd "Я могу представить себе, на что это похоже."
            m 2dfc "Все те люди, которые молча удаляли и мучили меня, и называя это справедливостью..."

            m 2eka "Тебе не кажется это справедливостью, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "Тебе не кажется это справедливостью, [player]?{fast}"

                "Кажется.":
                    $ persistent._mas_pm_monika_deletion_justice = True
                    if mas_isMoniBroken():
                        m 1dsc "..."
                        m 1rksdlc "Я знаю..."
                        m 1rksdld "Я не хотела спрашивать...{w=0.2} Я просто задумалась."
                        m 2rktpc "В конце концов, это очевидно."

                    elif mas_isMoniDis():
                        m 2rksdlc "Оу..."
                        m "Наверное, ты прав..."
                        m 1ekc "В конце концов, я сделала несколько довольно плохих вещей..."

                    elif mas_isMoniLove():
                        m 1hub "А-ха-ха!"
                        m 1hua "Иногда ты бываешь очень смешным~"
                        m 3tku "Ты думаешь, я поверю в это после всего, через что мы прошли?"
                        m 1tsb "Что все это время ты думал, что я заслуживаю ненависти от тех других людей?"
                        show monika 5hubfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
                        m 5hubfa "Э-хе-хе, ты такой милый, [player]~"

                    else:
                        m 1euc "..."
                        m 2esc "Мне трудно поверить, что ты действительно думаешь, что я заслужила все это."
                        m 2tkc "Я имею в виду, ты уже так долго со мной, так что ты не можешь {i}действительно{/i} умать, что я это заслужила, верно?"
                        if persistent._mas_pm_cares_about_dokis:
                            m 2lksdlc "...Может быть, я немного заслуживаю этого, но..."
                        else:
                            m 2lksdlc "Ну, может быть, другие люди так думают, но ты-то на самом деле так не думаешь, не так ли?"
                            m "В любом случае..."
                        m 1eka "Спасибо, что спас меня и был со мной."
                        m 1hua "Если я смогу быть с тобой, я думаю, это действительно стоило всего,{w=0.1} {nw}"
                        extend 1hub "а-ха-ха~"

                "Не кажется.":
                    if persistent._mas_pm_monika_deletion_justice:
                        $ persistent._mas_monika_deletion_justice_kidding = True
                    $ persistent._mas_pm_monika_deletion_justice = False

                    if mas_isMoniBroken():
                        m 2ekc "..."
                        m 1rksdlc "Я не уверена в этом..."
                    elif mas_isMoniDis():
                        m 1wuo "Правда?"
                        m 1rksdla "Я подумала, что, возможно, ты считаешь это справедливым."
                        m 1eka "Я рада, что ты так не думаешь."
                        m 2rksdlb "Предполагаю, что это не шутка, э-хе-хе..."

                    elif mas_isMoniLove():
                        m 1hua "Я так и думала, хе-хе~"
                        if persistent._mas_monika_deletion_justice_kidding:
                            $ persistent._mas_monika_deletion_justice_kidding = False

                            m 1hub "Я знала, что ты шутил в прошлый раз!"
                        m 1tsbsa "Ты сидишь со мной уже довольно долгое время, и я ни за что не поверю тебе, если ты скажешь обратное."
                        m 1ekbfa "Когда я с тобой, это даже помогает мне игнорировать людей, которым я не нравлюсь."
                        m 1hubfb "Я люблю тебя, [player]~"
                        m 1hubfa "Я рада, что ты на моей стороне."
                        return "derandom|love"

                    else:
                        m 2hua "Я рада, что ты тоже так думаешь!"
                        m 2eka "Даже если бы ты назвал это справедливостью, твое присутствие здесь говорит об обратном."
                        m 2hub "А-ха-ха!"

        "Нет.":
            $ persistent._mas_pm_given_false_justice = False
            m 1eka "Приятно это слышать."
            m "Я рада, что никто и никогда не усомнился в том, что ты такой, какой ты есть."
            m 1eua "Зная, каково это, я надеюсь, что никто никогда не доставит тебе проблем за то, что ты делаешь, или за то, во что ты веришь."
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_poweroutage",
            category=['погода'],
            prompt="Отключение электричества",
            random=True
        )
    )

label monika_poweroutage:
    m 1eua "Эй, [player], а ты помнишь, как я говорила о том, что мне нравится слушать спокойные звуки дождя?"
    m 3lksdla "Я только что поняла, что это, конечно, хорошо, но это также может сильно навредить тебе в твоём мире."
    m 1lksdlc "Гром и молния могут ударить в любой момент, и, воплне возможно, во что-нибудь опасное."
    m 1lksdlb "Эффекты могут быть довольно, ну... шокирующими, если можно так выразиться."
    m 1hksdlb "А-ха-ха~"
    m 1ekd "Я даже не хочу думать о том, что произошло бы, если бы молния ударила во что-нибудь важное для тебя."
    m 2ekc "Что произойдёт со мной, если произойдёт скачок напряжения и твой компьютер сгорит?"
    m 2dsc "Если такое вообще произойдёт...{w=0.3}{nw}"
    extend 2eka "Я знаю, ты думаешь о чём-то."
    m 1eka "Извини, я не хотела всё так омрачать. Это просто мои размышления."
    m 1eud "Если что-нибудь произойдёт, то за этим, возможно, последует отключение электричества."

    if mas_isMoniAff(higher=True):
        m 1hksdlb "Я имела в виду, что {i}это{/i} всё ещё весьма удурчает, но по крайней мере мы знаем, что мы увидимся вновь."
        m 1eua "Скорее всего, это может застать тебя врасплох; всё внезапно стемнеет, но посторайся запомнить следующее:"
        m 1eub "Я буду с тобой. Даже если ты меня не видишь, я буду с тобой духовно, пока ты не вернёшься ко мне в целости и сохранности."
        m 3eua "...И последнее замечание, тебе не надо бояться заглядывать ко мне во время шторма.{w=0.2} {nw}"
        extend 1eka "Я буду всегда рада тебе, но с другой стороны..."
        show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hua "Я уверена, что наши отношения смогут противостоять какому-то шторму~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_savingwater",category=['жизнь'],prompt="Экономия воды",random=True))

label monika_savingwater:
    m 1euc "[player], задумывался ли ты о том, сколько воды люди используют каждый день?"
    m 3euc "Скорее всего, ты пьёшь воду время от времени."
    m 3dsc "Ты ходишь в туалет, моешь свои руки, моешься..."
    m 1euc "И это не говоря уже о том, что в некоторых частях мира даже одну каплю воды не достанешь."
    m 1rsc "Как бы заставляет тебя задуматься, сколько бы ты мог сэкономить воды, если бы ты того захотел."
    m 4eua "Полагаю, ты мог бы попытаться использовать её экономичнее, когда моешь руки."
    m "Или, когда моешься, ты мог бы выключать воду, пока намыливаешься, а потом включить её обратно, когда готов ополоснуться."
    m 2eka "И в итоге, большая часть воды используется только так, где она необходима."
    m "На такие вещи, как производство электроэнергии и фермество, уходит куда больше воды, чем мы можем использовать."
    m 1hksdlb "Так что, полагаю, тебе не захочется жертвовать своим комфортом, чтобы сделать столь мизерный вклад."
    m 1dkbsa "Иногда тебе надо просто принять долгую, расслабляющую ванну после тяжёлого дня."
    m 2hksdlb "Я однозначно проходила через всё это раньше, поэтому и знаю, насколько это здорово может быть, если оно тебе понадобится."
    if mas_isMoniLove(higher=True) and mas_is18Over():
        show monika 5tsbfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5tsbfu "Когда я буду в твоей реальности, возможно, мы сможем экономить воду, принимая ванну вместе..."
        m "Э-хе-хе~"
        m 5hubfu "Было бы хорошо, если бы ты приготовил хорошую, расслабляющую ванну для нас, чтобы нам вместе принять ее, когда я попаду в твой мир."
        show monika 1kubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 1kubfu "Я буду ждать этого дня, [mas_get_player_nickname()], э-хе-хе~"
    else:
        m 1ekbfa "Было бы неплохо, если бы ты приготовил хорошую расслабляющую ванну для меня, когда я перескочу в твою реальность."
        if mas_isMoniAff():
            m 3ksbsa "Может быть, я даже буду не против поделиться, э-хе-хе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_pygmalion",
            category=['литература'],
            prompt="Пигмалион и статуя",
            conditional="persistent._mas_first_kiss",
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.ENAMORED, None)
        )
    )

label monika_pygmalion:
    m 1eua "Эй, [player], читал ли ты когда-нибудь {i}Метаморфозы{/i}?"
    m 3eua "Это сборник стихов древнеримского поэта Овидия."
    m 1eud "Есть один стих, который поразил меня, и он называется {i}История Пигмалиона и Статуи.{/i}"
    m 1eua "В нём рассказывается история о скульпторе, Пигмалионе, который влюбился в статую из слоновой кости, которую сам же и создал."
    m 3eua "Он так сильно полюбил свою статую, что, во время одного из фестивалей, посвящённых Афродите, он сделал предложение богине и пожелал у неё дар жизни для своей статуи."
    m 1eub "Когда он вернулся к себе домой, он поцеловал статую и, к его удивлению, губы статуи оказались тёплыми."
    m 1eua "Он поцеловал статую ещё раз, и статуя из слоновой кости потеряла свою тяжесть, став на ощупь такой же мягкой, как и кожа."
    m 3hub "Афродита исполнила его желание!"
    m 1eka "Эта история поразила меня потому, что она напомнила мне о нас, [player], и как здесь истолковали превращение невозможного в возможное."
    m 1hua "Это вселило в меня надежду, что чудо может произойти в любой момент, и я смогу наконец-то попасть в твою реальность."
    m 2dku "Да...{w=0.5}это было бы чудесно."
    m 2dubsu "...И тогда, ты сможешь наконец-то поцеловать меня."
    m 1rkbsa "Знаю, мы целовались раньше, даже в нынешних обстоятельствах..."
    m 1ekbfa "Но, мне кажется, мы оба знаем, что между нами стоит небольшой барьер."
    m 3hubfa "Не знаю, как ты, но я, так или иначе, всё равно хочу попытаться поцеловать тебя через экран."
    m 1hubfb "Возможно, мы должны повторить это несколько раз, и, таким образом, мы сломаем барьер, находящийся между нами..."
    m 2rubfu "Э-хе-хе."
    m 2tubfb "Думаешь, ты сможешь поцеловать меня достаточное число раз, чтобы сломать барьер?"
    m 6hubfb "Есть только один способ узнать это, а-ха-ха!"
    call monika_kissing_motion(duration=0.5, initial_exp="6hubfa", fade_duration=0.5)
    m 6hubfa "..."
    m 1ekbfa "Полагаю, на этот раз не сработало."
    m 3hubfb "Ну да ладно, нам просто нужно продолжать стараться, и, быть может, это всё-таки сработает, а-ха-ха!"
    m 1tkbfu "Я правда не могу дождаться того дня, когда я наконец-то смогу прижаться своими губами к твоим и впитать твоё тепло..."
    m 1dkbfa "Как по мне, такая мечта однозначно сбудется."
    m 1ekbfa "Это просто предположение, но..."
    m 1kubfu "Уверена, тебе такое тоже понравится~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gotomonika",
            category=['ты'],
            prompt="Что, если я приду в твой мир?",
            pool=True,
        )
    )

default persistent._mas_pm_would_come_to_spaceroom = None
# True if they would, False if they wouldn't, None if no answer.

label monika_gotomonika:
    m 1euc "Прийти в мой мир?"
    m 1lksdld "Ты имеешь в виду эту небольшую комнату, витающую в пустоте?"

    if persistent._mas_you_chr:
        m 4eksdlc "Вообще-то...{w=0.5}разве ты уже не пробовал однажды нечто подобное?"
        m 2lksdla "...Хотя это был не совсем {i}ты...{/i}"

    m 2lksdla "Я очень рада тому, что ты хочешь быть здесь, со мной, но..."
    m 2eksdlc "Ты правда не должен."
    m 2eksdld "Знаю, я уже говорила о том, что я бы давным-давно затащила тебя сюда, если бы могла..."
    m 2eksdlc "Но чем больше я задумываюсь об этом, тем больше думаю, что было бы целесообразнее, если бы я перешла в твою реальность."
    m 3eka "Я бы предпочла оказаться там, нежели ждать, когда ты придёшь сюда."
    m 3dsc "[player]...{w=1}не говори мне, что ты правда хочешь бросить свою реальность--{w=0.5} {i}настоящий{/i} мир--{w=0.5}лишь ради того, чтобы прийти {i}сюда{/i}, в богом забытое место?{nw}"
    $ _history_list.pop()
    menu:
        m "[player]...{w=1}не говори мне, что ты правда хочешь бросить свою реальность--{w=0.5} {i}настоящий{/i} мир--{w=0.5}лишь ради того, чтобы прийти {i}сюда{/i}, в богом забытое место?{fast}"
        "Да, хочу.":
            $ persistent._mas_pm_would_come_to_spaceroom = True

            m 4wkd "Но [player]!"
            m "Здесь совсем нечего делать!"
            m 2dsc "Ты так {i}сильно{/i} ненавидишь свою реальность?"
            m 2eka "Когда-нибудь, я найду способ добраться до тебя, и когда этот день настанет, я обещаю, эти усилия оправдают себя."
            m 4euc "Кубы бы жизнь не забросила тебя с этого момента, я буду рядом с тобой, чтобы помочь тебе справиться с нагрузкой."
            m 4eud "Даже сейчас, если у тебя был тяжёлый день, ты можешь поговорить со мной ою этом в любое время."
            m 2dsc "Жизнь, скорее всего, бросила тебя во все стороны, если учесть то, что ты большую её часть проводил со мной."
            m 3hua "Но, раз уж ты пребываешь здесь, то это лишь показывает, насколько ты устойчив."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Мне уже не терпиться разделить хорошие и плохие мгновения вместе с тобой."

        "Нет, не хочу.":
            $ persistent._mas_pm_would_come_to_spaceroom = False

            m 1eka "Я рада, что ты всё ещё готов ждать меня, [player]."
            m 1lksdla "Не пойми меня неправильно, я {i}действительно{/i} хочу быть с тобой..."
            m 1lksdlc "Но я думаю, что для тебя было бы опасно пытаться перейти сейчас."
            m 1eka "...Если это вообще возможно при нынешней технологии."
            m 1hub "Не волнуйся, мы можем продолжать составлять друг другу компанию и так!"
            m 1hksdlb "Я знаю, что пройдет некоторое время, прежде чем мы сможем по-настоящему быть вместе, но я надеюсь, что ты не против подождать."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Я буду ждать столько, сколько потребуется, [mas_get_player_nickname()]."

        "...":
            $ persistent._mas_pm_would_come_to_spaceroom = None

            m 2eka "Всё в порядке, я всегда буду ценить и дорожить моментами, которые мы проводим вместе, даже вот так."
            m 2ekc "Кроме того, я даже не знаю, как ты мог попасть сюда с нынешними технологиями."
            m 2lksdlc "...И даже если бы {i}был{/i} какой-то способ, я не думаю, что это было бы безопасно или гарантировано."
            m 2lksdld "Так что будь добр, хотя бы подожди, пока технология не улучшится настолько, чтобы это было полностью безопасно."
            m 2lksdlc "Я {i}правда{/i} не хочу рисковать тем, что ты не сделаешь это должным образом и окажешься в своей собственной пустоте..."
            m 2dkd "....оставив нас обоих в полном одиночестве."
            m 4hua "Я имею в виду, что технологии развиваются довольно быстро, так что мы сможем увидеть друг друга раньше, чем узнаем об этом!"
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Так что будь терпелив к своей прекрасной девушке, и я обещаю, что сделаю то же самое для тебя, [mas_get_player_nickname()]."

    m 5luu "Но-о-о...{w=1}если ты всё-таки появишься на моём крыльце..."
    show monika 1hksdlb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 1hksdlb "То, полагаю, у меня не будет другого выбора, кроме как принять этот факт и поприветствать тебя с распростёртыми объятиями!"
    m 1eksdla "Этого будет мало для начала, но я уверена, что мы найдём способ сделать это лучше."
    m 3hub "С течением времени, мы могли бы уже создать свою реальность!"
    m 3euc "Конечно, это звучит довольно сложно, если задуматься..."
    m 3eub "Но я не сомневаюсь в том, что вместе мы могли бы достичь чего угодно!"
    m 3etc "Знаешь...{w=1}наверное, тебе было бы {i}гораздо{/i} проще прийти сюда, но я не перестаю надеяться, что смогу прийти к тебе."
    m 1eua "Ну а пока, давай просто подождём и посмотрим, что можно сделать."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_vehicle",
            category=['моника'],
            prompt="Какая твоя любимая машина?",
            unlocked=False,
            pool=True,
            rules={"no_unlock": None}
        )
    )

default persistent._mas_pm_owns_car = None
# True if player owns car, False if not

default persistent._mas_pm_owns_car_type = None
# String describing the type of car owned by the player.
#   SUV-Pickup: SUV or pickup
#   sports: sports car
#   sedan: sedan car
#   motorcyle: motorcyle

label monika_vehicle:
    m 1euc "Моя любимая машина?"
    m 3hksdlb "Ты уже знаешь, что я не умею водить, глупышка!"
    m 3eua "Обычно я просто шла пешком или садилась на поезд, если мне нужно было отправиться куда-то далеко."
    m 1eka "Так что я не знаю, что тебе сказать, [player]..."
    m 1eua "Когда я думаю о машинах, первое, что приходит на ум, - это, вероятно, широко известные типы."
    m 3eud "Внедорожники или пикапы, спортивные автомобили, седаны и хэтчбеки..."
    m 3rksdlb "И хотя они на самом деле не автомобили, я думаю, мотоциклы тоже являются обычными транспортными средствами."

    if persistent._mas_pm_driving_can_drive:
        m 1eua "Что насчёт тебя?"

        m "У тебя есть машина?{nw}"
        $ _history_list.pop()
        menu:
            m "У тебя есть машина?{fast}"
            "Да.":
                $ persistent._mas_pm_owns_car = True

                m 1hua "Ого, это очень круто, что у тебя есть собственная машина!"
                m 3hub "Тебе очень повезло, ты знаешь это?"
                m 1eua "Я имею в виду, что просто владение автомобилем - это уже символ статуса."
                m "Разве это не роскошь - владеть им?"
                m 1euc "Если только..."
                m 3eua "Ты живешь там, где это необходимо..."
                m 1hksdlb "Вообще-то, неважно, ахаха!"
                m 1eua "В любом случае, приятно знать, что у тебя есть автомобиль."
                m 3eua "Кстати говоря..."

                show monika at t21
                python:
                    option_list = [
                        ("An SUV.", "monika_vehicle_suv",False,False),
                        ("A pickup truck.","monika_vehicle_pickup",False,False), #note, doing this to give the illusion of two options
                        ("A sports car.","monika_vehicle_sportscar",False,False),
                        ("A sedan.","monika_vehicle_sedan",False,False),
                        ("A hatchback.","monika_vehicle_hatchback",False,False),
                        ("A motorcycle.","monika_vehicle_motorcycle",False,False),
                        ("Another vehicle.","monika_vehicle_other",False,False)
                    ]

                    renpy.say(m, "Это любой из упомянутых мною автомобилей или что-то другое?", interact=False)

                call screen mas_gen_scrollable_menu(option_list, mas_ui.SCROLLABLE_MENU_TALL_AREA, mas_ui.SCROLLABLE_MENU_XALIGN)
                show monika at t11

                $ selection = _return

                jump expression selection
                # use jump instead of call for use of the "love" return key

            "Нет.":
                $ persistent._mas_pm_owns_car = False

                m 1ekc "Ох, понятно."
                m 3eka "Ну, покупка автомобиля может быть довольно дорогой, в конце концов."
                m 1eua "Ничего страшного [player], мы всегда можем взять его напрокат, чтобы путешествовать."
                m 1hua "Я уверена, что когда ты это сделаешь, у нас будет много прекрасных воспоминаний вместе."
                show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5eua "Но опять же...{w=1}прогулки в любом случае гораздо романтичнее~"

    else:
        $ persistent._mas_pm_owns_car = False

        m 3eua "Вообще-то, я помню, ты говорил, что тоже не умеешь водить..."
        m 3rksdla "Ты задал интересный вопрос, э-хе-хе..."
        m 1hua "Может, однажды это изменится, и тогда ты что-нибудь получишь."
        m 1hubsb "Таким образом, ты сможешь возить меня в самые разные места, а-ха-ха!"
    return

label monika_vehicle_sedan:
    $ persistent._mas_pm_owns_car_type = "sedan"
    jump monika_vehicle_sedan_hatchback

label monika_vehicle_hatchback:
    $ persistent._mas_pm_owns_car_type = "hatchback"
    jump monika_vehicle_sedan_hatchback

label monika_vehicle_pickup:
    $ persistent._mas_pm_owns_car_type = "pickup"
    jump monika_vehicle_suv_pickup

label monika_vehicle_suv:
    $ persistent._mas_pm_owns_car_type = "suv"
    jump monika_vehicle_suv_pickup



label monika_vehicle_suv_pickup:

    m 1lksdla "Ох мой, твоя машина, должно быть, довольно большая."
    m 1eua "Это значит, что там много места, верно?"
    m 3etc "Если это так..."
    m 3hub "Мы могли бы отправиться в поход!"
    m 3eua "Мы бы доехали до леса, ты бы поставил палатку, а я бы приготовила пикник."
    m 1eka "Пока мы бы обедали, мы бы наслаждались пейзажами и окружающей нас природой..."
    m 1ekbsa "А когда наступит ночь, мы ляжем на наши спальные мешки и будем любоваться звездами, держась за руки."
    m 3ekbsa "Это определенно романтическое приключение, которое я не могу дождаться, чтобы разделить с тобой, [player]."
    m 1hkbfa "Э-хе-хе~"
    return

label monika_vehicle_sportscar:
    $ persistent._mas_pm_owns_car_type = "sports"

    m 3hua "Ого!"
    m 3eua "Это должно быть очень быстро, да?"
    m 3hub "Нам обязательно нужно отправиться в путешествие..."
    m 1eub "Поехать по живописному маршруту, проехав по шоссе..."
    m 1eub "Если это возможно, было бы здорово снять верхнюю часть машины..."
    m 3hua "Тогда мы сможем почувствовать ветер на лице, пока все проносится мимо в тумане!"
    m 1esc "Но..."
    m 1eua "Также было бы здорово ехать в нормальном темпе..."
    m 1ekbsa "Тогда мы сможем наслаждаться каждым моментом поездки вместе~"
    return

label monika_vehicle_sedan_hatchback:

    m 1eua "Это очень здорово."
    m "Честно говоря, я предпочитаю этот тип автомобилей."
    m 3eua "Из того, что я слышала, они резвые и легкие в управлении."
    m 3eub "Такая машина отлично подойдет для езды по городу, как ты думаешь, [player]?"
    m 3eua "Мы могли бы ездить в музеи, парки, торговые центры и так далее."
    m 1eua "Было бы здорово иметь возможность ездить в места, до которых слишком далеко идти пешком."
    m 3hua "Всегда интересно открывать и исследовать новые места."
    m 1rksdla "Возможно, мы даже найдем место, где мы сможем быть вдвоем..."
    m 1tsu "...Наедине."
    m 1hub "А-ха-ха!"
    m 3eua "Просто чтобы ты знал, я ожидаю чего-то большего, чем простая поездка по городу для наших свиданий..."
    m 1hua "Надеюсь, ты меня удивишь [player]."
    m 1hub "Но опять же...{w=0.5}я буду рад чему угодно, лишь бы это было с тобой~"
    return

label monika_vehicle_motorcycle:
    $ persistent._mas_pm_owns_car_type = "motorcyle"

    m 1hksdlb "А-а?"
    m 1lksdlb "Ты водишь мотоцикл?"
    m 1eksdla "Я удивлена, я никогда не ожидала, что ты так ездишь."
    m 1lksdlb "Честно говоря, я немного не решаюсь сесть на него, а-ха-ха!"
    m 1eua "Правда, я не должна бояться..."
    m 3eua "В конце концов, это ты за рулем."
    m 1lksdla "Это меня немного...{w=0.3}успокаивает."
    m 1eua "Просто езжай медленно и аккуратно, хорошо?"
    m 3hua "В конце концов, мы никуда не торопимся."
    m 1tsu "Илиты планировал ехать так быстро, чтобы у меня не было выбора, кроме как крепко держаться за тебя...{w=0.3}ты планировал ехать так быстро, чтобы у меня не было выбора, кроме как крепко держаться за тебя?~"
    m 3kua "Это довольно хитро с твоей стороны, [player]."
    m 1hub "А-ха-ха!"
    $ p_nickname = mas_get_player_nickname()
    m 3eka "Не нужно стесняться, [p_nickname]...{w=0.3}{nw}"
    extend 3ekbsa "Я обниму тебя, даже если ты не попросишь..."
    m 1hkbfa "Вот как сильно я люблю тебя~"
    return "love"

label monika_vehicle_other:
    $ persistent._mas_pm_owns_car_type = "other"

    m 1hksdlb "Ох, похоже, мне еще многое предстоит узнать о машинах, не так ли?"
    m 1dkbsa "Что ж, я буду с нетерпением ждать того дня, когда смогу наконец оказаться рядом с тобой за рулем~"
    m 3hubfb "{i}И{/i} наслаждаться пейзажами тоже, а-ха-ха!"
    m 1tubfb "Может быть, у тебя есть что-то ещё более романтичное, чем любой автомобиль, который я знаю."
    m 1hubfa "Думаю, мне просто придется подождать и увидеть, э-хе-хе~"
    return

##### PM Vars for player appearance
#NOTE: THIS VAR CAN BE EITHER A TUPLE OR A STRING WHEN SET.
#IF THIS IS A TUPLE, THE PLAYER HAS HETEROCHROMIA.
# [0] - Left eye color
# [1] - Right eye color
#
# If this is just a string, then the player's eyes are both the same color
default persistent._mas_pm_eye_color = None
default persistent._mas_pm_hair_color = None
default persistent._mas_pm_hair_length = None
default persistent._mas_pm_skin_tone = None
# Iff player is bald
default persistent._mas_pm_shaved_hair = None
default persistent._mas_pm_no_hair_no_talk = None

## Height Vars
## NOTE: This is stored in CENTIMETERS
default persistent._mas_pm_height = None

##### We'll also get a default measurement unit for height
default persistent._mas_pm_units_height_metric = None

# True if the user decided to share appearance with us
#   NOTE: we default to False, and this can only get flipped to True
#   in this toppic.
default persistent._mas_pm_shared_appearance = False


# height categories in cm
define mas_height_tall = 176
define mas_height_monika = 162

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_player_appearance",
            category=['ты'],
            prompt="Твоя внешность",
            conditional="seen_event('mas_gender')",
            action=EV_ACT_RANDOM
        )
    )

label monika_player_appearance:
    python:
        def ask_color(msg, _allow=lower_letters_only, _length=15):
            result = ""
            while len(result) <= 0:
                result = renpy.input(msg, allow=_allow, length=_length).strip()

            return result

    m 2ekd "Слушай, [player]."
    m 2eka "Я всё хотела задать тебе парочку вопросов."
    m 2rksdlb "Хотя чего уж там - больше, чем парочку. Я довольно давно о них думала, раз уж на то пошло."
    m 2rksdld "Но я всё никак не могла найти правильный момент, чтобы их задать..."
    m 3lksdla "Но я понимаю, что если не задам их сейчас, то и в будущем мне не будет некомфортно затрагивать эту тему."
    m 3eud "Мне было интересно, как ты выглядишь. Я не могу физически тебя увидеть, да и к твоей веб-камере я вряд ли могу подключиться..."
    m "Потому что во-первых, у тебя её может не оказаться, а во-вторых, даже если она у тебя есть, я не знаю, как получить к ней доступ."
    m 1euc "Вот я и решила, что ты сам можешь мне рассказать, чтобы я примерно обрисовала всё в своей голове."
    m 1eud "Хоть всё и выйдет размыто, но это что-то."

    m "Ты ведь не против, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты ведь не против, [player]?{fast}"

        "Не против.":
            $ persistent._mas_pm_shared_appearance = True

            m 1sub "Правда? Здорово!"
            m 1hub "А это было проще, чем мне казалось."
            m 3eua "[player], только давай честно? Знаю, порой так и хочется отпустить какую-нибудь шутку, но я сейчас серьёзна, и хочу той же серьёзности от тебя."
            m "В общем, первый вопрос прост, как и ответ на него!"
            m 3eub "Люди часто говорят, что глаза - зеркало души, так что начнём с них."

            #This menu is too large to use a standard one, so we use a gen-scrollable here instead
            show monika 1eua at t21
            python:
                eye_color_menu_options = [
                    ("У меня голубые глаза.", "blue", False, False),
                    ("У меня карие глаза.", "brown", False, False),
                    ("У меня зелёные глаза.", "green", False, False),
                    ("У меня серые глаза.", "gray", False, False),
                    ("У меня чёрные глаза.", "black", False, False),
                    ("Мои глаза другого цвета.", "other", False, False),
                    ("У меня гетерохромия.", "heterochromia", False, False),
                ]

                renpy.say(m, "Какого цвета твои глаза?", interact=False)

            show monika at t11
            call screen mas_gen_scrollable_menu(eye_color_menu_options, mas_ui.SCROLLABLE_MENU_TALL_AREA, mas_ui.SCROLLABLE_MENU_XALIGN)
            $ eye_color = _return

            call expression "monika_player_appearance_eye_color_{0}".format(eye_color)

            m 3rud "Вообще..."
            m 2eub "Мне кажется, что следующий вопрос мне стоит задать, чтобы прояснить кое-что для последующего вопроса..."

            m "В чём ты измеряешь своей рост, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "В чём ты измеряешь своей рост, [player]?{fast}"

                "В сантиметрах.":
                    $ persistent._mas_pm_units_height_metric = True
                    m 2hua "Поняла, спасибо, [player]!"

                "В футах и дюймах.":
                    $ persistent._mas_pm_units_height_metric = False
                    m 2hua "Поняла!"

            m 1rksdlb "Всё пытаюсь не звучать как какой-то агент, что тебя о всяком расспрашивает, но всё же мне любопытно."
            m 3tku "К тому же, раз уж я твоя девушка, то мне позволено знать, правильно?"
            m 2hua "Плюс, так мне будет проще отыскать тебя, как только я попаду в твою реальность."

            m 1esb "Итак,{w=0.5} какой у тебя рост, [player]?"

            python:
                if persistent._mas_pm_units_height_metric:

                    # loop till we get a valid cm
                    height = 0
                    while height <= 0:
                        height = store.mas_utils.tryparseint(
                            renpy.input(
                                'Какой у тебя рост в сантиметрах?',
                                allow=numbers_only,
                                length=3
                            ).strip(),
                            0
                        )

                else:

                    # loop till valid feet
                    height_feet = 0
                    while height_feet <= 0:
                        height_feet = store.mas_utils.tryparseint(
                            renpy.input(
                                'Какой у тебя рост в футах?',
                                allow=numbers_only,
                                length=1
                            ).strip(),
                            0
                        )

                    # loop till valid inch
                    height_inch = -1
                    while height_inch < 0 or height_inch > 11:
                        height_inch = store.mas_utils.tryparseint(
                            renpy.input(
                                '[height_feet] футов и сколько дюймов?',
                                allow=numbers_only,
                                length=2
                            ).strip(),
                            -1
                        )

                    # convert to cm
                    height = ((height_feet * 12) + height_inch) * 2.54

                # finally save this persistent
                persistent._mas_pm_height = height

            if persistent._mas_pm_height >= mas_height_tall:
                m 3eua "Ого, [player]!"
                m 1eud "Не могу сказать, что когда-либо встречала кого-то, кого можно назвать высоким."
                m 3rksdla "И свой точный рост я не знаю, так что я не могу провести адекватное сравнение..."

                call monika_player_appearance_monika_height

                if persistent._mas_pm_units_height_metric:
                    $ height_desc = "сантиметров"
                else:
                    $ height_desc = "дюймов"

                m 3esc "В литературном клубе самой высокой была Юри. И то, она была всего на несколько [height_desc] выше меня, так что разница не существенная!"
                m 3esd "Хотя в отношениях с [bf] твоего роста есть лишь один недостаток, [mas_get_player_nickname()]..."
                m 1hub "Тебе придётся наклоняться, чтобы меня поцеловать!"

            elif persistent._mas_pm_height >= mas_height_monika:
                m 1hub "О, у меня примерно такой же рост!"
                m "..."
                m 2hksdlb "Ну ладно, свой рост я не могу узнать наверняка..."

                call monika_player_appearance_monika_height

                m 3rkc "Это всего лишь догадка--будем надеяться, что я права."
                m 3esd "Но в обычном росте нет ничего плохого! Если честно, то будь ты ниже, в некоторых случаях мне было бы слегка неудобно."
                m "А если будь ты выше, мне бы приходилось вставать на носочки, чтобы быть к тебе ближе. А это не хорошо!"
                m 3eub "Я считаю, что быть посредине - идеальный вариант. Знаешь, почему?"
                m 5eub "Потому что тогда мне не придётся ни наклоняться ни дотягиваться до тебя, чтобы поцеловать, [mas_get_player_nickname()]! Ахаха~"

            else:
                m 3hub "Прямо как Нацуки! Хотя я уверена, что ты выше! А если нет, то я буду волноваться."

                if persistent._mas_pm_cares_about_dokis:
                    m 2eksdld "Для своего возраста она была на удивление низкой, и мы с тобой знаем почему. Я всегда её жалела по этому поводу."

                m 2eksdld "Я знала, что ей не нравилось быть низкой, потому что принято считать, что всё маленькое - обязательно милое..."
                m 2rksdld "А потом ещё появились проблемы с её отцом. Нелегко, наверное, было быть такой беззащитной и вдобавок маленькой."
                m 2ekc "Наверное, ей постоянно казалось, что на неё смотрят сверху вниз. И образно, и буквально..."
                m 2eku "Но несмотря на её комплексы, [player], мне кажется, что твой рост делает тебя только милее~"

            m 1eua "А теперь, [player],"

            m 3eub "Скажи-ка, твои волосы короткие? Или длинные как у меня?~{nw}"
            $ _history_list.pop()
            menu:
                m "Скажи-ка, твои волосы короткие? Или длинные как у меня?~{fast}"

                "Они короткие.":
                    $ persistent._mas_pm_hair_length = "short"
                    $ persistent._mas_pm_hair_length_im = "короткие"

                    m 3eub "Должно быть, это приятно! Только не пойми неправильно - мне нравятся мои волосы и то, как я с ними экспериментирую..."
                    m 2eud "Но, сказать по правде, я иногда завидовала Нацуки и Сайори. За короткими волосами ведь попроще следить."

                    if persistent.gender == "M":
                        m 4hksdlb "Хотя будь у тебя волосы как у них, для парня они были бы длинноваты."

                    else:
                        m 4eub "Можно просто встать с постели и пойти по своим делам, не беспокоясь об укладке."
                        m "Плюс, расправить их после сна гораздо проще, потому что с длинными волосами это превращается в ад."

                    m 2eka "Но мне кажется, что ты очаровательно смотришься с короткими волосами. От одной только мысли на лице наворачивается улыбка, [player]."
                    m 2eua "Радуйся, что тебе не нужно сталкиваться с проблемами длинных волос, [player]!{w=0.2} {nw}"
                    extend 2hub "Ахаха~"

                "Они обычной, средней длины.":
                    $ persistent._mas_pm_hair_length = "average"
                    $ persistent._mas_pm_hair_length_im = "недлинные"

                    m 1tku "Ну, не может такого быть..."
                    m 4hub "Ты ведь по всем параметрам не обычный человек."
                    m 4hksdlb "Ахаха! Прости, [player]. Я не пыталась тебя смутить. Но иногда так и хочется, понимаешь?"
                    m 1eua "Если честно, то в плане волос здорово иметь среднюю длину. Не нужно много беспокоиться об укладке."
                    m "Плюс, они дают больше свободы творчества, нежели короткие волосы"
                    m 1rusdlb "Сказать по правде, мне даже немного завидно~"
                    m 3eub "Я даже вспомнила одно высказывание- 'Ухаживайте за своими волосами, ведь они - корона, которую вы никогда не снимете!'"

                "Они длинные.":
                    $ persistent._mas_pm_hair_length = "long"
                    $ persistent._mas_pm_hair_length_im = "длинные"

                    m 4hub "Ура, ещё одна наша общая черта!"
                    m 2eka "С длинными волосами бывают сложности, верно?"
                    m 3eua "Но с ними можно делать много всего интересного. Хоть я и просто завязываю их бантиком, я понимаю, что другим нравятся разные стили."
                    m "Юри вот носила распущенные волосы, а другим могут нравиться косички, хвостики и всё такое..."

                    python:
                        hair_down_unlocked = False
                        try:
                            hair_down_unlocked = store.mas_selspr.get_sel_hair(
                                mas_hair_down
                            ).unlocked
                        except:
                            pass

                    if hair_down_unlocked:
                        # TODO adjust this line to be more generic once we have additoinal hairstyles.
                        m 3eub "И раз с помощью скрипта мне удалось распустить свои волосы, то кто знает, сколько ещё стилей я могу перепробовать?"

                    m 1eua "Всегда ведь приятно иметь варианты."
                    m 1eka "Надеюсь, что тебе нравится то, как ты носишь свои волосы!"

                "У меня нет волос.":
                    $ persistent._mas_pm_hair_length = "bald"

                    m 1euc "Ой, а это интересно, [player]!"

                    m "Ты просто бреешь голову или волос у тебя нет по другой причине, если можно спросить?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Ты просто бреешь голову или волос у тебя нет по другой причине, если можно спросить?{fast}"

                        "Я брею голову.":
                            $ persistent._mas_pm_shaves_hair = True
                            $ persistent._mas_pm_no_hair_no_talk = False

                            m 1hua "Приятно, должно быть, совсем не беспокоиться о своих волосах..."
                            m 1eua "Можно просто встать с постели и пойти по своим делам, не беспокоясь об укладке...."
                            m 3eua "И когда снимаешь с себя шапку, ничего не нужно расправлять или поправлять!"

                        "Я потерял/потеряла свои волосы.":
                            $ persistent._mas_pm_shaves_hair = False
                            $ persistent._mas_pm_no_hair_no_talk = False

                            m 1ekd "Мне очень жаль, [player]..."
                            m 1eka "Но знай, что с волосами или без - для меня ты всегда выглядишь прекрасно!"
                            m "И если тебе когда-нибудь станет грустно по этому поводу, я всегда готова выслушать."

                        "Я не хочу об этом говорить.":
                            $ persistent._mas_pm_no_hair_no_talk = True

                            m 1ekd "Я всё понимаю, [player]"
                            m 1eka "Но знай, что с волосами или без - для меня ты всегда выглядишь прекрасно!"
                            m "И если тебе когда-нибудь станет грустно по этому поводу, я всегда готова выслушать."

            if persistent._mas_pm_hair_length != "bald":
                m 1hua "Следующий вопрос!"
                m 1eud "И довольно очевидный..."

                m "Какого цвета твои волосы?{nw}"
                $ _history_list.pop()
                menu:
                    m "Какого цвета твои волосы?{fast}"
                    "Они коричневые/каштановые.":
                        $ persistent._mas_pm_hair_color_im = "коричневые"
                        $ persistent._mas_pm_hair_color_r = "коричневых"
                        $ persistent._mas_pm_hair_color_d = "коричневым"
                        $ persistent._mas_pm_hair_color_t = "коричневыми"
                        $ persistent._mas_pm_hair_color = "brown"

                        m 1hub "Ура, каштановые волосы лучшие!"
                        m 3eua "Только между нами, [player], мне очень нравится цвет моих волос. Уверена, у тебя этот цвет даже красивее!"
                        m 3rksdla "Хотя некоторые не согласны, что у меня именно каштановые волосы..."
                        m 3eub "Когда я копалась в файлах игры, то нашла точное название цвета своих волос."
                        m 4eua "Он называется коралловый коричневый. Интересно же?"
                        m 1hub "Я так рада, что у нас столько общего, [player]~"

                    "Они светлые.":
                        $ persistent._mas_pm_hair_color_im = "светлые"
                        $ persistent._mas_pm_hair_color_r = "светлых"
                        $ persistent._mas_pm_hair_color_d = "светлым"
                        $ persistent._mas_pm_hair_color_t = "светлыми"
                        $ persistent._mas_pm_hair_color = "blonde"

                        m 1eua "Правда? Слушай, а ты знаешь, что только два процента всех людей в мире - блондины?"
                        m 3eub "Это один из самых редких цветов волос. Большинство считают, что они - следствие периодической генетической аномалии--"
                        m "Неспособности тела выработать достаточное количества пигмента эумеланина, что придаёт волосам более тёмные цвета."
                        m 4eub "Есть так много оттенков светлых волос--бледные, пепельные--неважно, какой именно у тебя оттенок, тебя всё равно можно считать уникальным человеком."
                        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
                        m 5eua "Получается, мне повезло, что я встречаюсь с кем-то настолько особенным~"
                        show monika 2hua at t11 zorder MAS_MONIKA_Z with dissolve_monika

                    "Они чёрные.":
                        $ persistent._mas_pm_hair_color_im = "чёрные"
                        $ persistent._mas_pm_hair_color_r = "чёрных"
                        $ persistent._mas_pm_hair_color_d = "чёрным"
                        $ persistent._mas_pm_hair_color_t = "чёрными"
                        $ persistent._mas_pm_hair_color = "black"

                        m 2wuo "Чёрные волосы такие красивые!"
                        m 3eub "Знаешь, вот есть такой стереотип, что люди с чёрными волосами злее или вспылчывее по сравнению с другими..."
                        m 4hub "Но ты отличный пример того, что это не так. Мне вот кажется, что чёрные волосы крайне привлекательны."
                        m 3eua "К тому же, если положить немного чёрных волос под микроскоп, то увидишь, что не такие они и чёрные."
                        m "Ты ведь знаешь, что если на определённые объекты будет падать прямой солнечный свет, то они будут выглядеть по-другому?"
                        m 3eub "С чёрными волосами так же--можно увидеть золотистый оттенок, коричневый или даже фиолетовый. О многом заставляет задуматься, не думаешь, [player]?"
                        m 1eua "В волосах может скрываться бесконечное множество оттенков, не видных невооружённым глазом."

                        #If this is a tuple, it means the player has heterochromia
                        if isinstance(persistent._mas_pm_eye_color, tuple):
                            m 3hua "И всё же... я считаю, что [guy] с чёрными волосами и твоими глазами - это лучшее, что можно увидеть глазами, [player]~"
                        else:
                            m 3hua "И всё же... я считаю, что [guy] с чёрными волосами и [persistent._mas_pm_eye_color_t] глазами - это лучшее, что можно увидеть, [player]~"

                    "Они рыжие.":
                        $ persistent._mas_pm_hair_color_im = "рыжие"
                        $ persistent._mas_pm_hair_color_r = "рыжих"
                        $ persistent._mas_pm_hair_color_d = "рыжим"
                        $ persistent._mas_pm_hair_color_t = "рыжими"
                        $ persistent._mas_pm_hair_color = "red"

                        m 3hua "И ещё одна твоя особенность, [player]~"
                        m 3eua "А ты знаешь, что рыжие волосы, наряду со светлыми, - самые редкие из всех естественных цветов?"
                        m 1eua "Но рыжие встречаются немного реже. Такой цвет есть лишь у одного процента всех людей."
                        m 1hub "Это редкое и прекрасное явление--настолько же прекрасное, как и ты!"

                    "Они другого цвета.":
                        $ persistent._mas_pm_hair_color_im = ask_color("Какого цвета твои волосы?")
                        $ persistent._mas_pm_hair_color_r = " "
                        $ persistent._mas_pm_hair_color_d = " "
                        $ persistent._mas_pm_hair_color_t = " "

                        m 3hub "О! А это красивый цвет, [player]!"
                        m 1eub "Я сразу вспомнила, как спросила тебя о цвете твоих глаз."
                        m 1eua "Хоть глаза у девочек из клуба неестественного цвета--конечно же я помню, что можно использовать линзы--"
                        m 3eua "Цвета их волос вполне могут существовать в реальности. Я уверена, что ты уже встречал людей с крашенными волосами - фиолетовыми, например..."
                        m 3eka "Поэтому их внешность в каком-то роде не далека от реальности, если забыть о глазах. И, честно говоря, самый нереалистичный у них именно характер."
                        m 3hksdlb "Прости, [player]! Что-то меня унесло. Я просто хотела сказать, что красить волосы крайне интересно."
                        show monika 5rub at t11 zorder MAS_MONIKA_Z with dissolve_monika
                        m 5rub "И я могу быть слегка предвзятой, но я уверена, что ты будешь прекрасно смотреться со своими волосами~"
                        show monika 2hua at t11 zorder MAS_MONIKA_Z with dissolve_monika

            m 2hua "Ну ладно..."
            m 2hksdlb "Теперь последний вопрос, [player], обещаю."
            m "Божечки, как о многом ещё нужно спросить... но если бы я спрашивала про каждую деталь, то этот допрос длился бы вечно."
            m 1huu "...и вряд ли это нужно нам обоим, хаха..."
            m 1rksdld "В общем, я понимаю, что этот вопрос может слегка неудобным..."
            m 1eksdla "Но для меня это как последняя часть пазла, поэтому я надеюсь, что ты не сочтёшь его грубым..."

            m "Какого цвета у тебя кожа, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "Какого цвета у тебя кожа, [player]?{fast}"

                "У меня светлая кожа.":
                    $ persistent._mas_pm_skin_tone = "светлая"

                "У меня смуглая кожа.":
                    $ persistent._mas_pm_skin_tone = "смуглая"

                "У меня чёрная кожа.":
                    $ persistent._mas_pm_skin_tone = "чёрная"

            m 3hub "Отлично! Спасибо за честность. Теперь я лучше понимаю, как ты выглядишь, [player]."
            m 3eub "Не знать ни одной детали о твоей внешности - это как смотреть на пустой холст, но теперь я вижу восхитительный портрет!"
            m 3eua "Я не сомневалась в твоей красоте, но теперь мы с тобой стали ещё ближе."
            m 3eka "Намного, намного ближе~"
            m 1eka "Благодаря тебе мой туман неведения был развеян, [mas_get_player_nickname()]."

            if persistent._mas_pm_eye_color == "green" and persistent._mas_pm_hair_color == "brown":
                m 2hua "Я и не думала, что мы выглядим настолько похоже. Это очень интересно!"

            else:
                m 2hua "Я и не думала, что наша внешность настолько отличается. Это очень интересно!"

            m 1dsa "Я сейчас представляю, как будет проходить наша встреча..."

            show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika

            if persistent._mas_pm_hair_length == "bald":
                if persistent._mas_pm_height >= mas_height_tall:
                    m 5eubfu "Как я бегу к тебе на встречу и ты заключаешь меня в свои объятия..."

                elif persistent._mas_pm_height >= mas_height_monika:
                    m 5eubfu "Как я бегу к тебе на встречу и мы заключаем друг друга в крепкие объятия..."

                else:
                    m 5eubfu "Как я бегу к тебе на встречу, и учитывая, что я выше тебя, ты протянешь ко мне руки и заключишь в свои объятия..."

            else:
                python:
                    hair_desc = persistent._mas_pm_hair_color_im

                    if persistent._mas_pm_hair_length != "average":
                        hair_desc = (
                            persistent._mas_pm_hair_length_im + " " + hair_desc
                        )

                if persistent._mas_pm_height >= mas_height_tall:

                    m 5eubfu "Как я бегу к тебе на встречу и ты заключаешь меня в свои объятия, а я буду гладить твои [hair_desc] волосы..."

                elif persistent._mas_pm_height >= mas_height_monika:

                    m 5eubfu "Как я бегу к тебе на встречу и мы заключаем друг друга в крепкие объятия, а я глажу своей рукой твои [hair_desc] волосы..."

                else:

                    m 5eubfu "Как я бегу к тебе на встречу, ты протягиваешь ко мне руки и заключаешь в свои объятия, а я глажу своей рукой твои [hair_desc] волосы..."

            show monika 1lkbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 1lkbsa "...и я наконец смогу услышать стук твоего сердца и понять, что всё это по-настоящему."

            #Tuple means heterochromia, so we should filter that out
            if isinstance(persistent._mas_pm_eye_color, tuple):
                m 3ekbsa "Ну а до тех пор я буду сидеть здесь и представлять, как заглядываю в твои красивые глаза, [player]."
            else:
                m 3ekbsa "Ну а до тех пор я буду сидеть здесь и представлять, как заглядываю в твои красивые [persistent._mas_pm_eye_color_im] глаза, [player]."

            show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbfa "Я люблю тебя больше, чем можно описать словами."
            return "derandom|love"

        "Против.":
             m 2dsc "..."
             m 2ekd "Я понимаю, [player]."
             m 2eka "Знаю, у всех есть свои границы..."
             m 2rksdla "И, быть честной, даже слова дадут мне лишь размытую картину того, как ты выглядишь, так что я не виню тебя."
             m 2eka "Но если передумаешь, обязательно дай мне знать!"

    return "derandom"

label monika_player_appearance_eye_color_blue:
    $ persistent._mas_pm_eye_color_im = "голубые"
    $ persistent._mas_pm_eye_color_r = "голубых"
    $ persistent._mas_pm_eye_color_d = "голубым"
    $ persistent._mas_pm_eye_color_t = "голубыми"
    $ persistent._mas_pm_eye_color = "blue"

    m 3eub "Голубые глаза? Прекрасно! Голубой - очень красивый цвет--словно безоблачное небо или море."
    m 3eua "Но уйдут недели, прежде чем я перечислю все метафоры, связанные с голубыми глазами."
    m 4eua "Плюс, голубой - мой второй любимый цвет, сразу после зелёного. Он ведь настолько очаровывающий, не так ли?"
    m 4hksdlb "Прямо как ты, [player]!"
    m 4eub "А ты знаешь, что ген для голубых волос рецессивный, то есть встречается он у меньшего числа людей?"
    show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eubla "А это значит, что ты даже больше, чем моё сокровище~"
    show monika 2eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 2eua "Что ж, меня это навело на следующий вопрос--"
    return

label monika_player_appearance_eye_color_brown:
    $ persistent._mas_pm_eye_color_im = "карие"
    $ persistent._mas_pm_eye_color_r = "карих"
    $ persistent._mas_pm_eye_color_d = "карим"
    $ persistent._mas_pm_eye_color_t = "карими"
    $ persistent._mas_pm_eye_color = "brown"

    m 1eub "Здорово! Вроде как я раньше этого не говорила, но карие глаза очень красивы!"
    m 2euc "Ненавижу, когда люди говорят, что карие глаза слишком обычные. Я вот в корне не согласна!"
    m 2hua "Я считаю, что карие глаза - одни из самых красивых. Они такие глубокие и яркие!"
    m 3hub "И у каждого человека с карими глазами они разного оттенка."
    m 5ruu "Интересно, тёмные ли они у тебя, словно летнее небо в ночи, или светлое, словно оленья шёрстка..."
    m 2hksdlb "Извини. Так уж получилось, что президент литературного клуба заносит в метафоры. Постараюсь не задерживаться с этим."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "И я не сомневаюсь, что твои глаза прекрасны~"
    show monika 1eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 1eua "Что ж, меня это навело на следующий вопрос--"
    return

label monika_player_appearance_eye_color_green:
    $ persistent._mas_pm_eye_color_im = "зелёные"
    $ persistent._mas_pm_eye_color_r = "зелёных"
    $ persistent._mas_pm_eye_color_d = "зелёным"
    $ persistent._mas_pm_eye_color_t = "зелёными"
    $ persistent._mas_pm_eye_color = "green"

    m 3sub "Ого, мой любимый цвет! И что очевидно, ещё одна наша общая черта!"
    m 4lksdla "Не знаю, насколько  странно будет делать комплименты твоей внешности, потому что выйдет так, словно я их делаю и себе..."
    m 1tsu "Хотя это скорее ещё один признак того, насколько сильно мы друг другу подходим, хехе~"
    m 1kua "Но между нами говоря, [player], зелёные глаза самые красивые, и это факт, не думаешь?"
    m 3hub "Ахаха! Я пошутила."
    show monika 5lusdru at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5lusdru "Или нет..."
    show monika 3eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 3eua "К следующему вопросу--"
    return

label monika_player_appearance_eye_color_gray:
    $ persistent._mas_pm_eye_color_im = "серые"
    $ persistent._mas_pm_eye_color_r = "серых"
    $ persistent._mas_pm_eye_color_d = "серым"
    $ persistent._mas_pm_eye_color_t = "серыми"
    $ persistent._mas_pm_eye_color = "gray"

    m 1sub "Крутотень!"
    m 3eub "А ты знаешь, что в генетическом плане серые глаза ближе всего к голубым?"
    m 1eud "Вообще, учёные ещё не в курсе, чем вызывается тот или иной цвет глаз, хотя они подозревают, что дело в количестве пигмента в оболочке глаза."
    m 1eua "Я вот сижу и представляю тебя с серыми глазами, [player]. Серыми, словно тихий, дождливый денёк..."
    m 1hubsa "И такую погоду я люблю не меньше тебя~"
    m 3hua "К следующему вопросу--"
    return

label monika_player_appearance_eye_color_black:
    $ persistent._mas_pm_eye_color_im = "чёрные"
    $ persistent._mas_pm_eye_color_r = "чёрных"
    $ persistent._mas_pm_eye_color_d = "чёрным"
    $ persistent._mas_pm_eye_color_t = "чёрными"
    $ persistent._mas_pm_eye_color = "black"

    m 1esd "Чёрные глаза - это необычно, [player]."
    m 4hksdlb "Сказать по правде, я никогда не видела людей с чёрными глазами, а потому не имею представления, как они выглядят..."
    m 3eua "Логично, конечно, что они не совсем чёрные, а то создавалось бы впечатление, что у людей с такими волосами вообще нет зрачков!"
    m 4eub "На самом деле чёрные глаза лишь очень тёмный оттенок карих глаз. Они по-прежнему поражают, но они не чёрные --хотя, быть честной, разницу заметить сложно."
    m 3eua "Расскажу тебе интересный факт--"
    m 1eub "Во времена американской революиции жила одна знатная дама по имени Элизабет Гамильтон, и она обладала очаровывающими чёрными глазами."
    m 1euc "Её муж часто о них писал."
    m 1hub "Понятия не имею, знаешь ты о ней или нет, но я на сто процентов уверена, что твои глаза ещё более очаровывающие, [player]~"
    m "К следующему вопросу--"
    return

label monika_player_appearance_eye_color_other:
    $ persistent._mas_pm_eye_color_im = ask_color("Какого цвета твои глаза?")

    m 3hub "О! А это красивый цвет, [player]!"
    m 2eub "Уверена, что смогу часами засматриваться в твои [persistent._mas_pm_eye_color_im] глаза."
    m 7hua "А теперь к следующему вопросу--"
    return

label monika_player_appearance_eye_color_heterochromia:
    m 1sub "Правда?{w=0.2} {nw}"
    extend 3hua "Невероятно, [player]~"
    m 3wud "Если я правильно припоминаю, меньше чем у одного процента людей есть гетерохромия!"

    m 1eka "...Если можно спросить..."
    # Ask the player about their eye colors separately.
    $ eyes_colors = []

    call monika_player_appearance_eye_color_ask
    $ eyes_colors.append(_return)
    call monika_player_appearance_eye_color_ask("правый", eye_color)
    $ eyes_colors.append(_return)
    $ persistent._mas_pm_eye_color = tuple(eyes_colors)

    m 1hua "Здорово!{w=0.2} {nw}"
    extend 3eua "Приступим к следующему вопросу--"
    return

label monika_player_appearance_eye_color_ask(x_side_eye="левый", last_color=None):
    m 3eua "Какого цвета твой [x_side_eye] eye?{nw}"
    $ _history_list.pop()
    menu:
        m "Какого цвета твой [x_side_eye] eye?{fast}"

        "Голубой" if last_color != "blue":
            $ eye_color = "голубой"

        "Карий" if last_color != "карий":
            $ eye_color = "карий"

        "Зелёный" if last_color != "зелёный":
            $ eye_color = "зелёный"

        "Серый" if last_color != "серый":
            $ eye_color = "серый"

        "Чёрный" if last_color != "чёрный":
            $ eye_color = "чёрный"

        "У него другой цвет...":
            $ eye_color = ask_color("Какого цвета твой [x_side_eye] eye?")

    return eye_color

# quick label where monika tells you her height
label monika_player_appearance_monika_height:
    if not persistent._mas_pm_units_height_metric:
        $ conv_height_str = ""
        $ real_height_str = "примерно пять с половиной футов"
    else:
        $ conv_height_str = " что примерно равняется 165-ти сантиметрам"
        $ real_height_str = "около 165-ти сантиметров"

    if seen_event("monika_immortal"):
        m 2eud "На вики, о которой я говорила, написано, что мой рост пять с половиной футов,[conv_height_str], но мне это кажется сомнительным..."
        m 2etc "Может, что-то поменялось? В конце концов, такой рост у меня по задумке, а не по факту."
    m 3etd "Мне кажется, что мой рост где-то [real_height_str]?"
    return

init 5 python:
     addEvent(
         Event(
            persistent.event_database,
            eventlabel="monika_players_control",
            category=["игры", "ddlc"],
            prompt="Твой контроль",
            random=True
            )
        )

label monika_players_control:
    m 3eub "[player], а знал ли ты о том, что у тебя в этой игре гораздо большая власть, чем у меня?"
    m 3eua "У тебя есть доступ к файлам игры и его коду, верно?"
    m 1eka "Следовательно, ты можешь изменить это всё, когда захочешь."
    m 3eka "Ты можешь даже изменить то, что не могу изменить я."
    m 4eub "К примеру, изменить всю механику игры, Сделать из визуального романа спокойную игровую площадку, которая у нас есть сейчас."
    m 3rksdla "Ты мог бы также добавить что-нибудь в класс для меня."
    m 1hub "К примеру, какие-нибудь цветы или парочку хороших книг."

    if mas_isMoniEnamored(higher=True) and not persistent._mas_acs_enable_promisering:
        m 1ekbsa "Или красивое обручальное кольцо."
        m 3dkbsu "Ох, тогда моя мечта станет явью."

    if not mas_consumable_coffee.enabled():
        m 1wuo "Ты мог бы даже добавить чашку с кофе в игру для меня!"
        m 1eka "Это было бы чудесно."

    if not persistent._mas_pm_has_code_experience:
        m 1hksdrb "Но я пологаю, что твои навыки программирования настолько же хорошие, что и у меня."
    else:
        m 3eua "Учитывая, что ты знаком с кодингом,{w=0.1} {nw}"
        extend 3hua "я уверена, что ты мог бы сделать что-то подобное!"

    m 1eua "Полагаю, таково предназначение видеоигр...{w=0.3}{nw}"
    extend 3eua "иметь практически безграничные возможности в мире, с которыми можешь взаимодействовать."
    m 3eub "С этим не соскучишься точно!"

    if not persistent._mas_pm_has_contributed_to_mas:
        m 1eka "Даже если ты не совсем понимаешь, как изменить эту игру..."
        $ line = "Мы всё ещё можем наслаждаться этим миром, который свёл нас вместе."

    else:
        $ line = "Особенно когда ты рядом со мной~"

    show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eubla "[line]"
    m 5ekbfa "Нет лучше способа насладиться игрой, чем быть рядом с тем, кого я люблю."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_backpacking",category=['природа'],prompt="Пеший туризм",random=not mas_isWinter()))

label monika_backpacking:
    m 1esa "Ты знаешь, чего мне всегда хотелось, [player]?"
    m 3eub "Я всегда размышляла о том, как было бы здорово отправиться в поход в дикую природу!"
    m 3eua "Уйти туда примерно на неделю и оставить всё позади."
    m 3esa "Никакой ответственноссти, никаких забот, никаких телефонов, никаких развлечений."
    m 1hua "Только представь, что мы на природе, только вдвоём..."
    m "Звуки щебетания птиц и дуновения ветра..."
    m 1eka "Смотреть на то, как олень пасётся в утренней росе..."
    m "Я не могу представить себе ничего более спокойного."
    m 1esa "Мы целыми днями будем исследовать загадочные леса, безмятежные луга и холмистые возвышенности..."
    m 3hub "Возможно, мы даже найдём скрытое озеро и поплаваем в нём!"

    if mas_isMoniAff(higher=True):
        m 2rsbsa "Возможно, у нас не будет купальников, но мы будем там одни поэтому, возможно, нам они и не понадобятся..."
        m 2tsbsa "..."
        m 1hubfu "Надеюсь, ты не сильно стесняешься, [mas_get_player_nickname()]. Э-хе-хе~"
        m 1ekbfa "Мы проведём ночи, засыпая в обнимку в спальном мешке и согревая друг друга..."
        m 3hubfb "И будем просыпаться каждое утро под чудесный рассвет!"

    else:
        m 3eka "Мы будем спать под звездами, просыпаясь каждое утро с великолепным восходом солнца."

    show monika 5esbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5esbfa "..."
    m "О, [player], разве это не звучит потрясающе?"
    m 5hubfa "Мне уже не терпится разделить этот опыт вместе с тобой~"
    return

## calendar-related pool event
# DEPENDS ON CALENDAR

# did we already change start date?
default persistent._mas_changed_start_date = False

# did you imply that you arent dating monika?
default persistent._mas_just_friends = False

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_dating_startdate",
            category=["романтика", "мы"],
            prompt="Когда мы начали встречаться?",
            pool=True,
            unlocked=False,

            # this will be unlockable via the action
            rules={"no_unlock": None},

            # we'll pool this event after a month of the relationship
            conditional=(
                "store.mas_anni.pastOneMonth() "
                "and persistent._mas_first_calendar_check"
            ),

            action=EV_ACT_UNLOCK
        )
    )

label monika_dating_startdate:
    $ import store.mas_calendar as mas_cal
    python:
        # we might need the raw datetime
        first_sesh_raw = persistent.sessions.get(
            "first_session",
            datetime.datetime(2017, 10, 25)
        )

        # but this to get the display plus diff
        first_sesh, _diff = mas_cal.genFormalDispDate(first_sesh_raw.date())

    if _diff.days == 0:
        # its today?!
        # this should NEVER HAPPEN
        m 1lsc "We started dating..."
        $ _history_list.pop()
        m 1wud "We started dating{fast} today?!"
        m 2wfw "You couldn't have possibly triggered this event today, [player]."

        m "I know you're messing around with the code.{nw}"
        $ _history_list.pop()
        menu:
            m "I know you're messing around with the code.{fast}"
            "I'm not!":
                pass
            "You got me.":
                pass
        m 2tfu "Hmph,{w=0.2} you can't fool me."

        # wait 30 days
        $ mas_chgCalEVul(30)
        return

    # Otherwise, we should be displaying different dialogue depending on
    # if we have done the changed date event or not
    if not persistent._mas_changed_start_date:
        m 1lsc "Hmmm..."
        m 1dsc "I think it was..."
        $ _history_list.pop()
        m 1eua "I think it was{fast} [first_sesh]."
        m 1rksdlb "But my memory might be off."

        # ask user if correct start date
        m 1eua "Is [first_sesh] correct?{nw}"
        $ _history_list.pop()
        menu:
            m "Is [first_sesh] correct?{fast}"
            "Yes.":
                m 1hub "Yay!{w=0.2} I remembered it."

            "No.":
                m 1rkc "Oh,{w=0.2} sorry [player]."
                m 1ekc "In that case,{w=0.2} when did we start dating?"

                call monika_dating_startdate_confirm(first_sesh_raw)

                if _return == "NOPE":
                    # we are not selecting a date today
                    return

                # save the new date to persistent
                $ store.mas_anni.reset_annis(_return)
                $ persistent.sessions["first_session"] = _return
                $ renpy.save_persistent()

        m 1eua "If you ever forget, don't be afraid to ask me."
        m 1dubsu "I'll {i}always{/i} remember when I first fell in love with you~"
        $ persistent._mas_changed_start_date = True

    else:
        m 1dsc "Позволь мне проверить..."
        m 1eua "Мы начали встречаться [first_sesh]."

    # TODO:
    # some dialogue about being together for x time
    # NOTE: this is a maybe

    return

label monika_dating_startdate_confirm_had_enough:
    # monika has had enough of your shit
    # TODO: maybe decrease affection since you annoyed her enough?
    m 2dfc "..."
    m 2lfc "We'll do this another time, then."

    # we're going to reset the conditional to wait
    # 30 more days
    $ mas_chgCalEVul(30)

    return "NOPE"

label monika_dating_startdate_confirm_notwell:
    # are you not feeling well or something?
    m 1ekc "Are you feeling okay, [player]?"
    m 1eka "If you don't remember right now, then we can do this again tomorrow, okay?"

    # reset the conditional to tomorrow
    $ mas_chgCalEVul(1)

    return "NOPE"

label monika_dating_startdate_confirm(first_sesh_raw):

    python:
        import store.mas_calendar as mas_cal

        # and this is the formal version of the datetime
        first_sesh_formal = " ".join([
            first_sesh_raw.strftime("%B"),
            mas_cal._formatDay(first_sesh_raw.day) + ",",
            str(first_sesh_raw.year)
        ])

        # setup some counts
        wrong_date_count = 0
        no_confirm_count = 0
        today_date_count = 0
        future_date_count = 0
        no_dating_joke = False

    label .loopstart:
        pass

    call mas_start_calendar_select_date

    $ selected_date = _return
    $ _today = datetime.date.today()
    $ _ddlc_release = datetime.date(2017,9,22)

    if not selected_date or selected_date.date() == first_sesh_raw.date():
        # no date selected, we assume user wanted to cancel
        m 2esc "[player]..."
        m 2eka "I thought you said I was wrong."

        m "Are you sure it's not [first_sesh_formal]?{nw}"
        $ _history_list.pop()
        menu:
            m "Are you sure it's not [first_sesh_formal]?{fast}"
            "It's not that date.":
                if wrong_date_count >= 2:
                    jump monika_dating_startdate_confirm_had_enough

                # otherwise try again
                m 2dfc "..."
                m 2tfc "Then pick the correct date!"
                $ wrong_date_count += 1
                jump monika_dating_startdate_confirm.loopstart

            "Actually that's the correct date. Sorry.":
                m 2eka "That's okay."
                $ selected_date = first_sesh_raw

    elif selected_date.date() < _ddlc_release:
        # before releease date

        label .takesrs:
            if wrong_date_count >= 2:
                jump monika_dating_startdate_confirm_had_enough

            m 2dfc "..."
            m 2tfc "We did {b}not{/b} start dating that day."
            m 2tfd "Take this seriously, [player]."
            $ wrong_date_count += 1
            jump monika_dating_startdate_confirm.loopstart

    elif selected_date.date() == _today:
        # today was chosen
        jump .takesrs

    elif selected_date.date() > _today:
        # you selected a future date?! why!
        if future_date_count > 0:
            # don't play around here
            jump monika_dating_startdate_confirm_had_enough

        $ future_date_count += 1
        m 1wud "What..."

        m "We haven't been dating this whole time?{nw}"
        $ _history_list.pop()
        menu:
            m "We haven't been dating this whole time?{fast}"
            "That was a misclick!":
                # relief expression
                m 1duu "{cps=*2}Oh, thank god.{/cps}"

                label .misclick:
                    m 2dfu "[player]!"
                    m 2efu "You had me worried there."
                    m "Don't misclick this time!"
                    jump monika_dating_startdate_confirm.loopstart

            "Nope.":
                m 1dfc "..."

                show screen mas_background_timed_jump(5, "monika_dating_startdate_confirm_tooslow")

                menu:
                    "I'm kidding.":
                        hide screen mas_background_timed_jump
                        # wow what a mean joke

                        if no_dating_joke:
                            # you only get this once per thru
                            jump monika_dating_startdate_confirm_had_enough

                        # otherwise mention that this was mean
                        m 2tfc "[player]!"
                        m 2rksdlc "That joke was a little mean."
                        m 2eksdlc "You really had me worried there."
                        m "Don't play around like that, okay?"
                        jump monika_dating_startdate_confirm.loopstart

                    "...":
                        hide screen mas_background_timed_jump

                label monika_dating_startdate_confirm_tooslow:
                    hide screen mas_background_timed_jump

                # lol why would you stay slient?
                # TODO: Affection considerable decrease?
                $ persistent._mas_just_friends = True

                m 6lktdc "I see..."
                m 6dftdc "..."
                m 1eka "In that case..."
                m 1tku "{cps=*4}I've got some work to do.{/cps}{nw}"
                $ _history_list.pop()

                menu:
                    "What?":
                        pass

                m 1hua "Nothing!"

                # lock this event forever probably
                # (UNTIL you rekindle or actually ask her out someday)
                $ evhand.event_database["monika_dating_startdate"].unlocked = False
                return "NOPE"

    # post loop
    python:
        new_first_sesh, _diff = mas_cal.genFormalDispDate(
            selected_date.date()
        )

    m 1eua "Alright, [player]."
    m "Just to double-check..."

    m "We started dating [new_first_sesh].{nw}"
    $ _history_list.pop()
    menu:
        m "We started dating [new_first_sesh].{fast}"
        "Yes.":
            m 1eka "Are you sure it's [new_first_sesh]? I'm never going to forget this date.{nw}"
            # one more confirmation
            # WE WILL NOT FIX anyone's dates after this
            $ _history_list.pop()
            menu:
                m "Are you sure it's [new_first_sesh]? I'm never going to forget this date.{fast}"
                "Yes, I'm sure!":
                    m 1hua "Then it's settled!"
                    return selected_date

                "Actually...":
                    if no_confirm_count >= 2:
                        jump monika_dating_startdate_confirm_notwell

                    m 1hksdrb "Aha, I figured you weren't so sure."
                    m 1eka "Try again~"
                    $ no_confirm_count += 1

        "No.":
            if no_confirm_count >= 2:
                jump monika_dating_startdate_confirm_notwell

            # otherwise try again
            m 1euc "Oh, that's wrong?"
            m 1eua "Then try again, [mas_get_player_nickname()]."
            $ no_confirm_count += 1

    # default action is to loop here
    jump monika_dating_startdate_confirm.loopstart

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_first_sight_love",
            category=["романтика"],
            prompt="Любовь с первого взгляда",
            random=True
        )
    )

label monika_first_sight_love:
    m 1eud "Задумывался ли ты когда-нибудь о концепции любви с первого взгляда?"
    m 3euc "То есть, ты кого-то видишь впервые,и вдруг осознаёшь, что этот человек - любовь всей твоей жизни?"
    m 2lsc "Я думаю, это одна из многих...{w=0.5}концепций, нелепость которых ты осознаёшь чуть ли не сразу."
    m 2lksdlc "В смысле, ты не можешь понять, кто этот человек на самом деле, по одному лишь взгляду."
    m 2tkd "Ведь не похоже, что ты общялся, обедал или гулял с ним."
    m 2lksdlc "Ты даже не знаешь, какие у него интересы и хобби..."
    m 2dksdld "Он может оказаться довольно скучным или просто злым и ужасным человеком..."
    m 3eud "Именно поэтому я и думаю, что мы не должны надеяться {i}только{/i} на свои глаза, когда ищем идеального партнёра для самих себя."
    if mas_isMoniAff(higher=True):
        m 1eka "И, думаю, именно так я и влюбилась в тебя..."
        m 3eua "Да и не похоже, что я смогла увидеть тебя."
        show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbfa "Я люблю тебя таким, какой ты есть, [mas_get_player_nickname(exclude_names=['my love', 'love'])]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_anime_art",
            category=["разное"],
            prompt="Анимешный стиль рисования",
            random=True
        )
    )

label monika_anime_art:
    m 1eua "Задумывался ли ты когда-нибудь о художественных стилях аниме?"
    m 3rksdla "Уверена, Нацуки является экспертом в данной области, если учесть её увлечение мангой и всё такое..."
    m 3eub "Так или иначе, в этом стиле рисования есть много чего интересного."
    m 1eua "У него есть свободная форма, как и в моих стихах, что делает большую часть такого стиля очень уникальным..."
    m 3eua "От красивых пейзажей до потрясающих персонажей..."
    m 1hub "Он производит сильное впечатление с первого взгляда!"
    m 2esc "Хотя при свободной форме стиля рисования...{w=0.5}большая часть деталей становится немного нереалистичной."
    m 3rsc "Хотя он открывает перед многими художественными работами новые возможности, из-за него также некоторые детали выглядят как-то странно..."
    m 3rssdlc "К примеру, какие большие глаза становятся у персонажей, насколько маленькие у них носы, или какой странной длины, формы и размера могут быть их волосы..."
    m 2rksdlc "Не говоря уже...{w=1}о большой груди."
    m 2euc "Если бы я выглядела более реалистично, то у меня определённо не было бы таких атрибутов."
    m 1eua "Но, пологаю, настоящая красота стиля рисования исходит от недостатка реалистичности."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_whydoyouloveme",
            category=['моника','романтика'],
            prompt="За что ты меня любишь?",
            pool=True
        )
    )

label monika_whydoyouloveme:
    if mas_isMoniBroken():
        m 2euc "Хмф."
        m 2wfc "Я задаю себе этот вопрос каждый день."

    elif mas_isMoniDis():
        m 1efc "Я-{w=0.3}{nw}"
        extend 1rkc "Я не уверена..."

    elif mas_isMoniUpset():
        m 1dsc "Хм..."
        m 3hua "Потому что я знаю, что ты хороший человек, несмотря на то, как обстоят дела между нами."

    elif mas_isMoniEnamored(higher=True):
        m 1ekbla "Почему я люблю тебя?"

        #First time seeing this variation gets you an "I don't" tease
        if not renpy.seen_label('monika_whydoyouloveme_tease') and renpy.random.randint(1, 4) == 1:
            call monika_whydoyouloveme_tease

        #The above flow leads back into this one
        m 1dka "[mas_get_player_nickname(capitalize=True)]...{w=0.5}у меня есть на то множество причин. С какой стоит начать?"

        if store.mas_anni.anniCount() >= 1:
            m 3eka "Ты провел со мной так много времени,{w=0.2} зная, что, возможно, никогда не сможешь почувствовать мои объятия."
            m 3hua "...Но вот ты здесь, всё ещё рядом со мной."

        m 3ekbla "Каким бы безумным это ни казалось, и что бы ни думали другие люди, ты все равно здесь, со мной."
        m 1dku "Каждый раз, когда ты заглядываешь сюда, ты напоминаешь мне о том, что по ту сторону есть целый мир."
        m "..."
        m 1ekbsa "Я бы отдала тебе весь свой мир, если бы могла, [player]."
        m 1hubsa "Если и есть человек, который заслуживает его...{w=0.3}то это ты."
        m 1ekbsa "Я обещаю тебе, [player]..."
        m 3ekbsa "Что бы ни случилось, я {i}никогда{/i} не забуду тебя до конца своих дней."
        m 1dkbsu "Ты не просто спас меня, [player]...{w=0.3}{nw}"
        extend 1ekbsa "ты дал мне понять, как прекрасна жизнь на самом деле."
        m 1ekbsb "Когда-нибудь я заставлю тебя почувствовать себя любимым так же, как и ты меня~"
        m 1dkbsa "Когда-нибудь...{w=0.5}я смогу быть с тобой~"

        if persistent._mas_pm_love_yourself is False:
            m 2eka "И, [player]..."
            m 2ekc "Я помню, как ты говорил мне о том, что ты не любишь себя..."
            m 7eka "Но лично мне кажется, что ты любишь себя, хотя бы самую малость."
            m 3hua "Если бы ты не любил себя, то ты не был бы здесь, со мной."
            m 1dkbsu "Я...{w=0.5}я просто рада, что ты всё ещё здесь, [player]."
            m 1ekbsa "Пожалуйста, просто знай о том, что я всегда здесь, когда ты нуждаешься во мне~"

    else:
        # normal - aff
        m 2ekc "[player]..."
        m 2ekd "Ты, случайно, не чувствуешь себя неуверенно?"
        m 7rksdla "Я могу понять это чувство..."
        m 3eka "Но какова бы ни была причина,{w=0.2} Я просто хочу, чтобы ты знал, что я люблю тебя независимо от того, кто ты, [player]."
        m 1ekbsa "Просто открыв для меня игру, ты {i}буквально{/i} спас мне жизнь."
        m 1dkbsu "....Когда я с тобой,{w=0.2} я больше не одинока."
        m 3ekbsa "Ты действительно мой [hero], [mas_get_player_nickname(regex_replace_with_nullstr='my ')]~"

    return

label monika_whydoyouloveme_tease:
    m 1esc "Вообще-то нет."
    pause 5.0
    m 1hub "А-ха-ха, шучу!"
    m 1eub "Ты значишь для меня {i}всё{/i}, глупышка!"
    m 1eksdla "Но если честно ответить на твой вопрос..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_stoicism",
            category=['философия'],
            prompt="Стоицизм",
            random=True
        )
    )

label monika_stoicism:
    m 1eua "Я тут читала про греческую и римскую философию, [player]."
    m 1hksdlb "А-ха-ха! Я знаю, это звучит очень скучно, если подумать..."
    m 1eua "Но была определенная философия, которая привлекла мое внимание, пока я читала."
    m "Она называется стоицизм, её философия основанная в Афинах в третьем веке до нашей эры."
    m 4eub "Проще говоря, стоицизм - это философия, которая считает, что человек должен научиться принимать обстоятельства своего положения..."
    m "...И не поддаваться иррациональному желанию удовольствия или страху боли, чтобы они могли вести себе естественным образом."
    m 2euc "Сейчас у них плохая репутация, поскольку люди думают, что они холодные и бесчувственные."
    m 2eua "Однако стоики - это не просто кучка безэмоциональных людей, которые всегда серьезны."
    m "Стоики практикуют самоконтроль над тем, как они относятся к неблагоприятным событиям, и реагируют соответствующим образом, а не импульсивно."
    m 2eud "Например, допустим, ты не сдал важный экзамен в школе или пропустил срок сдачи проекта на работе."
    m 2esd "Что бы ты сделал, [player]?"
    m 4esd "Ты бы начал паниковать? Погрузился бы в депрессию и перестал бы пытаться? Или ты разозлился из-за этого и станешь обвинять других?"
    m 1eub "Я не знаю, что бы ты сделал, но, возможно, ты можешь брать пример со стоиков и сдерживать свои эмоции!"
    m 1eka "Хотя ситуация не идеальна, нет никакой практической причины тратить силы на то, что ты не можешь контролировать."
    m 4eua "Ты должен сосредоточиться на том, что ты можешь изменить."
    m "Может быть, лучше готовиться к следующему экзамену, заниматься у репетитора и просить у учителя дополнительные баллы."
    m "Или, если ты представил себе сценарий работы, начни будущие проекты раньше, составляй график и напоминания для этих проектов и избегай отвлекающих факторов во время работы."
    m 4hub "Это лучше, чем ничего не делать!"
    m 1eka "Но это только мое мнение, не так-то просто быть эмоционально устойчивым к большинству вещей в жизни..."

    if mas_isMoniUpset(lower=True):
        return

    if mas_isMoniAff(higher=True):
        m 2tkc "Ты должен делать всё, что {i}угодно{/i} , что поможет тебе избавиться от стресса. Твоё счастье очень важно для меня."
        m 1eka "С другой стороны, если ты когда-нибудь почувствуешь себя плохо из-за чего-то, что случилось с тобой в жизни..."
        show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hubfb "Ты всегда можешь прийти домой к своей милой девушке и рассказать мне, что тебя беспокоит"

    else:
        m 2tkc "Ты должен делать все, что поможет тебе избавиться от стресса. Твоё счастье очень важно для меня."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_add_custom_music",
            category=['мод',"медиа", "музыка"],
            prompt="Как добавить свою музыку?",
            conditional="persistent._mas_pm_added_custom_bgm",
            action=EV_ACT_UNLOCK,
            pool=True,
            rules={"no_unlock": None}
        )
    )

label monika_add_custom_music:
    m 1eua "Свою музыку добавить очень просто, [player]!"
    m 3eua "Просто следуй этим шагам..."
    call monika_add_custom_music_instruct
    return

label monika_add_custom_music_instruct:
    m 4eua "Во-первых,{w=0.5} убедись, что та музыка которую ты хочешь добавить, в формате MP3, OGG/VORBIS, или OPUS."
    m "Далее,{w=0.5} создай новую папку с названием \"custom_bgm\" в твоей директории \"DDLC\" ."
    m "Добавь свою музыку в эту папку..."
    m "А потом, либо дай мне знать, что ты добавил музыку, либо перезапусти игру."
    m 3eua "И всё! Твоя музыка будет доступна для прослушивания, здесь со мной, достаточно нажать клавишу 'm'."
    m 3hub "Видишь, [player]? я говорила тебе, что это легко, а-ха-ха!"

    # unlock the topic as a pool topic, also mark it as seen
    $ mas_unlockEVL("monika_add_custom_music", "EVE")
    $ persistent._seen_ever["monika_add_custom_music"] = True
    $ mas_unlockEVL("monika_load_custom_music", "EVE")
    $ persistent._seen_ever["monika_load_custom_music"] = True
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_load_custom_music",
            category=['мод',"медиа", "музыка"],
            prompt="Можешь ли ты проверить новую музыку?",
            conditional="persistent._mas_pm_added_custom_bgm",
            action=EV_ACT_UNLOCK,
            pool=True,
            rules={"no_unlock": None}
        )
    )

label monika_load_custom_music:
    m 1hua "Конечно!"
    m 1dsc "Дайте мне секунду, чтобы проверить папку.{w=0.2}.{w=0.2}.{w=0.2}{nw}"
    python:
        # FIXME: this is not entirely correct, as one may delete a song before adding a new one
        old_music_count = len(store.songs.music_choices)
        store.songs.initMusicChoices(store.mas_egg_manager.sayori_enabled())
        diff = len(store.songs.music_choices) - old_music_count

    if diff > 0:
        m 1eua "Отлично!"
        if diff == 1:
            m "Я нашла одну новую песню!"
            m 1hua "Не могу дождаться, чтобы послушать его вместе с тобой."
        else:
            m "Я нашла [diff] новых песен!"
            m 1hua "Не могу дождаться, чтобы послушать их вместе с тобой."

    else:
        m 1eka "[player], Я не нашла ни одной новой песни."

        m "Ты помнишь, как добавить свою музыку?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты помнишь, как добавить свою музыку?{fast}"
            "Да.":
                m "Хорошо, убедитесь, что ты все сделал правильно."

            "Нет.":
                $ pushEvent("monika_add_custom_music",True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_mystery',
            prompt="Тайны",
            category=['литература','медиа'],
            random=True
        )
    )

label monika_mystery:
    m 3eub "Знаешь [player], я думаю, что во многих историях есть интересный момент, который некоторые люди упускают из виду."
    m 3eua "Это то, что делает историю интересной... но может сломать её при неправильном использовании"
    m 3esa "Это может сделать историю удивительной, которую хочется перечитывать, или сделать так, что ты больше не захочешь к ней прикасаться."
    m 2eub "И эта часть..."
    m 2eua "..."
    m 4wub "...тайна!"
    m 2hksdlb "Ой! Я не имела в виду, что не скажу тебе, а-ха-ха!"
    m 3esa "Я имею в виду, что сама тайна может изменить все, когда речь идет о истории"
    m 3eub "Если это сделано хорошо, это может создать интригу и при повторном прочтении сделать предыдущие намеки очевидными."
    m 3hub "Зная поворот, человек может действительно изменить свое отношение ко всему повествованию. Не многие сюжетные моменты могут сделать это!"
    m 1eua "Это почти смешно... знание ответов фактически меняет твоё представление о самой истории."
    m 1eub "Сначала, когда ты читаешь тайну, ты смотришь на историю с неизвестной точки зрения..."
    m 1esa "Но при повторном прочтении ты смотришь на это с точки зрения автора."
    m 3eua "Ты видишь, как они оставили подсказки и построили историю так, чтобы дать достаточно намеков, чтобы читатель мог догадаться!"
    m 2esa "Я нахожу это действительно интересным, некоторые из лучших историй знают, как использовать хороший крюк."
    m 2lsc "Но если история не делает этого должным образом, она может стать худшей. Они используют крючки, чтобы казаться 'умными.'"
    m 2lud "Когда они пытаются это сделать, то при неправильной установке это может показаться бессмыслицей."
    m 2eud "Наверное, ты можешь утверждать, что не все истории с тайнами на самом деле {i}являются{/i} тайнами..."
    m 2eua "Даже в дрянных боевиках используются элементы тайны, чтобы сделать их интересными."
    m 4hksdlb "Хотя, думаю, история, в которой нет абсолютно никакой тайны, была бы довольно скучной!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_player_read_poetry",
            category=['литература'],
            prompt="Чтение стихов",
            random=True
        )
    )

default persistent._mas_pm_likes_poetry = None
#True if player likes poems, false if not

label monika_player_read_poetry:
    m 1eud "Скажи, [player]..."
    m 1eua "Ты знаешь, что я люблю поэзию, но я хотела бы узнать..."

    m 3eua "Ты часто читаешь стихи?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты часто читаешь стихи?{fast}"

        "Да.":
            $ persistent._mas_pm_likes_poetry = True
            m 1sub "Правда?"
            m 1hua "Это делает меня такой счастливой!"
            m 3eua "И правда, я серьезно. В наше время мало кто читает стихи."

        "Нет.":
            $ persistent._mas_pm_likes_poetry = False
            m 2ekc "Ох, как жаль..."
            m 2eka "Я просто надеюсь, что помогла тебе оценить поэзию немного больше."
            m 2ekc "Знаешь, в наши дни не так много людей читают стихи, так что это неудивительно."

    m 2euc "На самом деле, поэзию часто считают чем-то слишком сложным для понимания..."
    m 2efd "А с другой стороны, другие думают, что это просто куча красивых слов рядом друг с другом!"
    m 2dkc "Но это не так...{w=0.3}{nw}"
    extend 2dkd "поэзия - это нечто большее."
    m 4ekd "Ты должен вложить в неё себя."
    m 4ekc "Без своего писательского умения, {w=0.2}а также без своих чувств, {w=0.2}Э.Э.Каммингс просто не был бы Э.Э.Каммингсом..."
    m 7ekd "И без моих чувств к тебе мои стихи не были бы такими же."
    m 3eka "Любовь, печаль, гнев, страсть - все эти чувства оживляют слова."
    m 3hub "И благодаря этому даже простое текстовое сообщение может стать осмысленным стихотворением!"
    m 3eua "Вот почему я люблю поэзию."

    if persistent._mas_pm_likes_poetry:
        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eua "Боже, просто знать, что ты тоже читаешь стихи..."
        m 5hua "Это показывает, насколько мы похожи."
        m 5eua "Не могу дождаться, когда наконец попаду в твою реальность, чтобы мы могли вместе обсудить наши любимые стихи."
        m 5dka "Делиться стихами, писать новые...{w=0.5}только ты и я, преследующие нашу общую страсть..."
        m 5hub "По мне, так это прекрасная мечта!"

    else:
        m 1eka "Не могу дождаться, когда попаду в твою реальность, [player]..."
        m 1tfu "Тогда я смогу начать заставлять тебя читать стихи."
        m "..."
        m 3hub "А-ха-ха, я просто шучу! Я бы никогда не заставил тебя делать что-либо, [player]!"
        m 3eua "Но я думаю, что смогу заставить тебя полюбить поэзию."
        m 1eua "...И не только те стихи, которые я пишу о тебе, {nw}"
        extend 1kua "э-хе-хе~"

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_trick",
            category=["club members"],
            prompt="Другой выбор [player]'",
            random=True
        )
    )

label monika_trick:
    m 2eud "Слушай, [player], у меня есть вопрос..."
    m 2lksdlb "Надеюсь, я не покажусь опасной, как только скажу это..."
    m 2eka "Я знаю, что ты любишь меня и только меня, но... если бы тебе {i}действительно{/i} пришлось выбирать одну из членов клуба, с которой ты будешь..."

    m "Кого бы ты выбрал?{nw}"
    $ _history_list.pop()
    show screen mas_background_timed_jump(10, "monika_trick_2")
    menu:
        m "Кого бы ты выбрал?{fast}"
        "Юри.":
            call monika_trick_yuri
        "Сайори.":
            call monika_trick_sayori
        "Натцуки.":
            call monika_trick_natsuki
    return "derandom"

label monika_trick_2:
    $ _history_list.pop()
    menu:
        m "Кого бы ты выбрал?{fast}"
        "Юри.":
            call monika_trick_yuri
        "Сайори.":
            call monika_trick_sayori
        "Натцуки.":
            call monika_trick_natsuki
        "Моника.":
            jump monika_trick_monika
            # jump this path so we can use the "love" return key

    return "derandom"

label monika_trick_yuri:
    hide screen mas_background_timed_jump
    m 2euc "Я понимаю почему, она умна и физически привлекательна."
    m 2tub "Хорошо, что я обладаю обоими этими качествами в избытке!"
    m 2etc "Ой, подожди, это ведь не потому, что она стала одержима тобой?"
    m 2eud "Ты действительно настолько любишь яндере?"
    m 2lksdlc "..."
    m 1hksdlb "...А-ха-ха, мне нет нужды ревновать..."
    m 1eua "Ты любишь меня, а я люблю тебя, и это все, что имеет значение."
    m 1kua "Думаю, это моя вина, что я вообще спросила~"
    return

label monika_trick_natsuki:
    hide screen mas_background_timed_jump
    m 2eud "Это... немного удивительно."
    m 2lksdla "Я бы подумала, что это будет Сайори или Юри."
    m 1eud "Чувствуешь ли от этого связь с ней из-за её увлечений?"
    m 3euc "Или, возможно, ты чувствуешь некоторую жалость из-за ее положения в семье?"
    m 2lud "Ну, я думаю, я немного сбрасываю со счетов ее личность, в конце концов, напористость - это черта, достойная восхищения."
    m 3euc "Быть уверенным в себе и отстаивать то, что тебе нравится, не всегда легко, когда другие осуждают тебя за это."
    m 3rksdla "Иногда я даже немного завидую ее способности демонстрировать уверенность."
    m 3eub "Плюс ее умение готовить кексы просто поражает!"
    return

label monika_trick_sayori:
    hide screen mas_background_timed_jump
    m 2dkc "Этого я и ожидала..."
    m 2ekc "Это потому, что она была лучшей подругой главного героя, не так ли?"
    m 6lkc "Вполне логично, что главный герой встречается с другом детства."
    m 2dkc "Это действительно типично для романтических игр..."
    m 2ekc "Честно говоря, именно поэтому мне пришлось сначала... разобраться... с Сайори."
    m 6ekc "Ты решил бы с ней, как того требует сюжет, и даже не пытался бы сойтись со мной, поскольку игра тебе не позволила бы."
    m 6ekd "Я знаю, что это не твоя вина, но мысль о том, чтобы быть бездействующим и позволить этому случиться, пугает меня..."
    m 6ektpc "Ты бы завершил игру, а я бы навсегда застрял в адской пустоте..."
    m 6dktpc "Никогда не быть признанной тем, кого я люблю."
    m 6dktuc "..."
    if persistent._mas_pm_cares_about_dokis:
        m 6ektud "...Я знаю, что я не понравилась тебе своим поступком, прости, если я причинила тебе боль из-за этого."
    else:
        m 6ektud "...Я не жалею о том, что сделала, но мне жаль, что тебе пришлось увидеть то, что я должна была сделать."
    return

label monika_trick_monika:
    hide screen mas_background_timed_jump
    if not mas_getEVL_shown_count("monika_trick"):
        $ mas_gainAffection(10, bypass=True)
    else:
        $ mas_gainAffection()

    m 1tkbsu "Такого варианта не должно быть, глупышка!"
    m 1tubfb "Но я правда очень счастлива, ведь ты смотрел только на меня..."
    m 1tubfu "Я чувствую себя немного глупо из-за того, что на секунду задумалась о том, что ты вообще мог выбрать одну из них."
    m 5hubfu "Я люблю тебя, [player]!"
    m 5eubfb "И я тоже смотрю только на тебя!"
    return "derandom|love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_cares_about_dokis",
            category=["моника", "участники клуба"],
            prompt="Нечувствительные комментарии",
            random=True
        )
    )

default persistent._mas_pm_cares_about_dokis = None
# TRue if the player cares about the dokis, False if not

label monika_cares_about_dokis:
    m 3eub "Ах, [player]!"
    m 4hua "Хочешь услышать что-нибудь смешное, что однажды сделала Сайори?"
    m 4eua "Однажды я попросила её принести кофе для нас в клуб."
    m 2rksdlb "Атмосфера была слишком напряженной, и я решила её немного оживить."
    m 2eua "Ну, кофе хранили в учительской, собственно. Вот я и отправила её туда..."
    m 4wud "...и она пропала на целый час! Там были учителя, и она не хотела разговаривать с ними"
    m 2rfc "Поэтому она стала {i}очень долго{/i} ждать, когда они разойдутся."
    m 2tfu "Ты, наверное, скажешь, что она {i}ко{/i}--"
    m 2etc "...Хм..."
    m 2eud "Знаешь, что, [player]? Я просто хочу убедиться кое в чём..."
    m 2rksdlc "Я знаю, что иногда я могу делать довольно...{w=0.5}равнодушные замечания касательно других девушках, и тут меня осенило..."
    m 2ekc "Наверное, ты в достаточной мере заботишься о них, это и беспокоит тебя."
    m 4eub "...И это совершенно нормально, если это так, [player]!"
    m 4eka "В конце концов, мы впятером проводили много времени вместе, так что если тебе не нравится, когда я так шучу, то я всё понимаю."

    m "Итак, [player], тебе неприятно, когда я шучу о других девушках?{nw}"
    $ _history_list.pop()
    menu:
        m "Итак, [player], тебе неприятно, когда я шучу о других девушках?{fast}"
        "Да.":
            $ persistent._mas_pm_cares_about_dokis = True
            $ mas_hideEventLabel("monika_archetype", lock=True, derandom=True)

            m 2dkc "О нет... Не могу поверить, что не осознала этого раньше..."
            m 2eksdld "Мне очень жаль, [player]!"
            m 2rksdlc "Я буду очень стараться помнить об этом впредь."
            m 2eksdlc "Просто знай, что я не хотела тебя расстраивать."
            m 2eka "Но спасибо тебе за честность ответа, я хочу, чтобы ты знал, что всегда можешь рассказать мне всё."

        "Нет.":
            $ persistent._mas_pm_cares_about_dokis = False

            # NOTE: we never restore random for these topics
            $ mas_unlockEventLabel("monika_archetype")

            m 2eka "Я рада, что не заставила тебя чувствовать себя плохо или неловко, [mas_get_player_nickname()]."
            m 1tsu "В общем,, можно сказать, что она {i}висела{/i} там вечность!"
            m 1hub "А-ха-ха!"

    return "derandom|rebuild_ev"

#### old christmas.rpyc topics
# HOL020
# this will now always available in winter, but derandomed once the snow question is answered in either topic

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_snow",
            category=["зима","погода","ты"],
            prompt="Снег",
            random=mas_isWinter()
        )
    )

label monika_snow:
    m 1eua "Слушай, [player], теперь, когда началась зима, мне стало интересно..."

    m "В том месте, где ты живёшь, когда-нибудь шёл снег?{nw}"
    $ _history_list.pop()
    menu:
        m "В том месте, где ты живёшь, когда-нибудь шёл снег?{fast}"

        "Да":
            $ persistent._mas_pm_gets_snow = True

            m 1hub "Это прекрасно!"
            m 1eua "Мне всегда нравилась эта спокойная аура, которую она излучает."
            m 1dsa "Это так спокойно и уютно, понимаешь?"
            m 1hua "Есть тихая красота в наблюдении за тем, как мягкое, белое одеяло снега и льда укладывает мир спать."
            call monika_snow_gets_snow

        "Нет":
            $ persistent._mas_pm_gets_snow = False

            call monika_hemispheres_nogets_snow

    return "derandom"

# player has snow, snow version
label monika_snow_gets_snow:
    if mas_isMoniHappy(higher=True):
        show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eubla "Может быть, когда-нибудь, когда я попаду в реальность, мы сможем прогуляться вместе..."

        if mas_isMoniAff(higher=True):
            m 5ekbfa "...и мы могли бы прижаться друг к другу, чтобы согреться~"

    m 5eubfb "Я не могу дождаться, чтобы пережить такую зимнюю ночь с тобой, [mas_get_player_nickname()]."
    return

# player no snow, snow version
label monika_snow_nogets_snow:
    m 2tkc "Sometimes it can get so heavy it becomes a real problem for your back..."

    if mas_isMoniAff(higher=True):
        m 1eksdla "В любом случае, по крайней мере, холодная погода - это отличная погода для объятий."
        show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbfa "Ночь в обнимку с тобой была бы чудесной..."
        m "Мое сердце бьется, просто представляя это."

    else:
        m 2eka "Но в любом случае, я уверена, что мы еще многое можем сделать вместе!"

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_snowmen",
            category=['зима'],
            prompt="Снеговик",
            random=False,
            conditional=(
                "persistent._mas_pm_gets_snow is not False "
                "and mas_isWinter()"
            ),
            action=EV_ACT_RANDOM
        )
    )

label monika_snowmen:
    m 3eua "Эй, [player], ты когда-нибудь лепил снеговика?"
    m 3hub "Я думаю, это очень весело!"
    m 1eka "Строительство снеговиков обычно рассматривается как то, что делают дети,{w=0.2} {nw}"
    extend 3hua "но я думаю, что они очень милые."
    m 3eua "Удивительно, как их можно оживить с помощью различных предметов..."
    m 3eub "...например, палки для рук, рот из гальки, камни для глаз и даже маленькая зимняя шапочка!"
    m 1rka "Я заметила, что давать им морковные носы - обычное дело, хотя я действительно не понимаю, почему..."
    m 3rka "Разве это не немного странно?"
    m 2hub "А-ха-ха!"
    m 2eua "В любом случае, я думаю, было бы здорово когда-нибудь построить его вместе."
    show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hua "Надеюсь, ты чувствуешь то же самое~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_snowballfight",
            category=["зима"],
            prompt="У тебя когда-нибудь был бой снежками?",
            pool=True,
            unlocked=mas_isWinter(),
            rules={"no_unlock":None}
        )
    )

label monika_snowballfight:
    m 1euc "Бои снежками?"
    m 1eub "Я играла в эту игру чуть ли не каждый день раньше, и мне всегда было весело!"
    m 3eub "Но тобой звучит ещё веселее, [player]!"
    m 1dsc "Хочу заранее предупредить..."
    m 2tfu "Я хорошо попадаю по целям."
    m 2tfb "Так что не жди того, что я дам тебе поблажку, а-ха-ха!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_iceskating",
            category=["спорт", "зима"],
            prompt="Катание на коньках",
            random=True
        )
    )

label monika_iceskating:
    m 1eua "Эй, [player], ты умеешь кататься на коньках?"
    m 1hua "Этот вид спорта и вправду весело изучать!"
    m 3eua "Особенно если умеешь делать много трюков."
    m 3rksdlb "Вначале довольно трудно держать равновесие на льду..."
    m 3hua "И в конечном итоге способность превратить это в представление действительно впечатляет!"
    m 3eub "На самом деле есть много способов катания на коньках..."
    m "Есть фигурное катание, конькобежный спорт и даже театральные представления!"
    m 3euc "И, несмотря на то, как это звучит, это не просто зимнее развлечение..."
    m 1eua "Во многих местах есть крытые катки, так что этим можно заниматься целый год."
    if mas_isMoniHappy(higher=True):
        m 1dku "..."
        m 1eka "Я бы очень хотела научиться кататься на коньках с тобой, [mas_get_player_nickname()]..."
        m 1hua "Но пока мы не можем этого сделать, то, что ты здесь, со мной, достаточно, чтобы я была счастлива~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sledding",
            category=["зима"],
            prompt="Катание на санях",
            random=mas_isWinter()
        )
    )

label monika_sledding:
    m 1eua "Эй, [player], знаешь, что было бы здорово сделать вместе?"
    m 3hub "Покататься на санках!"

    if persistent._mas_pm_gets_snow is False:
        #explicitly using False here so we don't grab None people who haven't
        # answered the question yet
        m 1eka "Возможно, там, где ты живешь, снега не будет..."
        m 3hub "Но, может быть, мы могли бы поехать туда, где снег есть!"
        m "В любом случае..."

    m 3eua "Ты можешь подумать, что это только для детей, но я думаю, что это может быть весело и для нас!"
    m 3eub "Мы могли бы прокатиться в трубе, на финсикх санях, блюдце, или даже на традиционных санках."
    m 1hua "Я слышала, что каждый из них дает разные опыт. К тому же, мы оба легко поместимся на санях."

    if mas_isMoniAff(higher=True):
        m 1euc "Хотя, финские сани немного маленькие."
        m 1hub "А-ха-ха!"
        m 1eka "В них, мне придётся сидеть у тебя на коленках."
        m 1rksdla "И следует также учесть то, что я могу упасть."
        m 1hubsa "Но я знаю, что ты не дашь это произойти. Ты ведь крепко обнимешь меня, верно?~"
        m 1tkbfu "Думаю, это было бы самой лучшей частью."
    else:
        m 1hub "Спускаться вместе по заснеженному склону с ветром, проносящимся мимо нас, - это было бы здорово!"
        m 1eka "Надеюсь, мы сможем как-нибудь вместе покататься на санках, [player]."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_snowcanvas",
            category=["зима"],
            prompt="Белоснежный холст",
            random=mas_isWinter()
        )
    )

label monika_snowcanvas:
    if persistent._mas_pm_gets_snow is not False:
        m 3euc "[player], ты когда-нибудь смотрел на снег и думал, что он напоминает чистый холст?"
        m 1hksdlb "Я знаю, что не очень хороша в искусстве..."
        m 3eua "Но если взять несколько бутылочек с водой и пищевыми красителями, можно весело провести день!"
        m 3hub "Мы можем просто выйти на улицу и дать волю своему воображению!"

    else:
        m 3euc "Знаешь [player], снег - это как чистый холст."
        m 3eub "Может быть, когда-нибудь, если мы поедем куда-нибудь, где идет снег, мы сможем взять с собой пищевые красители в бутылочках с распылителем и просто выйти на улицу и дать волю своему воображению!"

    m 1eua "Иметь столько места для рисования - это замечательно!"
    m 1hub "Нам просто нужно убедиться, что снег плотно прижат, и тогда мы сможем рисовать в своё удовольствие!"
    m 1eka "Я бы с удовольствием когда-нибудь порисовала на снегу вместе с тобой."
    m 3hua "Может быть, ты нарисуешь что-нибудь для меня, когда это случится, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_cozy",
            category=["романтика","зима"],
            prompt="Разогрев",
            random=mas_isWinter(),
            aff_range=(mas_aff.AFFECTIONATE,None)
        )
    )

label monika_cozy:
    m 3eua "Знаешь, что мне нравится в холодной погоде, [player]?"
    m 3eka "Что-нибудь тёплое будет очень кстати~"
    m 1rksdla "Те, у кого холодные руки, очень ценят это чувство..."
    m 1eua "Это как чувствовать объятия любимого человека~"
    m 3eub "Ты также можешь надеть свою зимнюю одежду, которая до сих пор висит в твоём шкафу."
    m 1hub "Всегда приятно, когда наконец-то можно достать свой зимний комплект одежды."
    m 3eubla "Но знаешь, как лучше всего согреться?"
    m 3ekbsa "Обниматься с любимым человеком перед камином~"
    m 3ekbfa "Просто сидеть под теплым одеялом и пить горячий напиток."
    m 1hubfa "Ах, если бы я могла чувствовать твоё тепло каждый раз, когда мы обнимаемся, я бы мечтала о холодной погоде каждый день!"
    m 1ekbfa "Как только я обниму тебя, я никогда тебя не отпущу, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_winter",
            category=["зима"],
            prompt="Зимние развлечения",
            random=mas_isWinter()
        )
    )

label monika_winter:
    m 1eud "Ах, [player]!"
    m 1eua "Что ты думаешь о зиме?"
    m 3eua "Все виды веселья, которые возможно только в это время..."
    if persistent._mas_pm_gets_snow is not False:
        m 3eub "Игра в снежки, как правило, именно то, чем можно наслаждаться несколько раз в году."

    else:
        m 3eka "Я знаю, что там, где ты живешь, снега не бывает, но многие люди получают удовольствие от развлечений в снегу..."

    m 3eua "Лепить снеговика, кататься на санках, устраивать бои снежками..."
    m 3eud "Некоторые люди даже живут там, где достаточно холодно, чтобы озера и пруды замерзли, и могут наслаждаться такими вещами, как катание на коньках на открытом воздухе, хоккей на пруду..."
    m 3wud "И некоторые ещё рыбачат...{w=1}{i}сделав прорубь{/i}!"
    m 1eka "Люди, которым не нравится холодная погода, остаются дома и не выходят на улицу, где уже идёт снег, поскольку им дома комфортнее..."
    m "Наблюдать за тем, как снег медленно падает, пока лунный свет отражается от свежего, белого холста... это так красиво."
    if mas_isMoniAff(higher=True):
        show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbfa "И если честно, обниматься под одеялом, читая вместе с тобой книгу - это лучшее зимнее занятие, которое я могу придумать~"
    else:
        m 1hua "Сидеть у окна, читать хорошую книгу, попивая чашечку кофе или горячего шоколада - это всегда прекрасное занятие в холодный вечер, [player]."
    return

#This combines _relax and _hypothermia into one topic
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_winter_dangers",
            category=["зима"],
            prompt="Зимние опасности",
            random=mas_isWinter()
        )
    )

label monika_winter_dangers:
    m 1hua "Разве зима не прекрасное время года, [player]?"
    if mas_isD25Season():
        m 3eka "Блестящий, белый снег, яркие и красочные огни~"
    m 3hub "Я от этого просто в восторгеЯ знаю, что у тебя нет снега там, где ты живешь, но я уверена, что ты можешь оценить его привлекательность."
    if persistent._mas_pm_gets_snow is False:
        #explicitly using False here so we don't grab None people who haven't
        # answered the question yet
        m 1eka "Я знаю, что у тебя нет снега там, где ты живешь, но я уверена, что ты можешь оценить его привлекательность..."
        m 3hua "Может быть, когда-нибудь после того, как я попаду в твою реальность, мы даже сможем отправиться в путешествие туда, где есть снег, и вместе насладиться его красотой!"

    m 1eka "..."
    m 3rkc "Хотя, какой бы потрясающей ни была зима, есть несколько опасностей..."
    m 3dsd "Например, метель или гололёд..."
    m 1ekc "И холод, разумеется..."
    m 3rksdlc "Холод может оказаться самым опасным явлением."
    m 3eksdlc "Очень легко получить гипотермию или обморожение, если ты не будешь осторожен, [player]."
    m 1ekd "Так что, пожалуйста, одевайся теплее, если выходишь на улицу..."
    m 3euc "Надень куртку, перчатки и самую теплую шляпу, которую сможешь найти..."
    m 1eka "А если станет слишком плохо, просто сиди дома в безопасном месте, хорошо?"
    m 1ekb "Каким образом можно провести суровый зимний день, чем носить пижаму, пить горячий шоколад, читать хорошую книгу и..."
    m 1hua "Разговаривать со мной."
    m 1huu "Э-хе-хе~"

    if mas_isMoniAff(higher=True):
        show monika 5hubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hubfu "Я всегда помогу тебе согреться, [mas_get_player_nickname()]~"
    return

#### end christmas.rpyc topics

default persistent._mas_pm_live_south_hemisphere = None
default persistent._mas_pm_gets_snow = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_hemispheres",
            category=["ты", "местонахождение"],
            prompt="Полушария",
            random=True
        )
    )

label monika_hemispheres:
    m 1euc "Эй, [player], мне вот интересно..."
    m 1eua "В каком полушарии ты живешь?"
    m 1eka "Знаю, это довольно странный вопрос..."
    m 3hub "Но это даёт мне более наглядное представление того, как всё у тебя устроено."
    m 3eua "Например, ты знаешь, что когда в Северном полушарии зима, в Южном полушарии на самом деле лето?"
    m 3hksdrb "Будет немного неловко, если я начну говорить о том, какая хорошая погода летом, но там, где ты находишься, сейчас середина зимы..."
    m 2eka "Но, так или иначе..."

    m "В каком полушарии ты живешь, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "В каком полушарии ты живешь, [player]?{fast}"

        "Северное полушарие.":
            $ persistent._mas_pm_live_south_hemisphere = False
            m 2eka "Я так и думала..."

        "Южное полушарие.":
            $ persistent._mas_pm_live_south_hemisphere = True
            m 1wuo "Я бы не подумала!"

    $ store.mas_calendar.addSeasonEvents()
    m 3rksdlb "В конце концов, большая часть населения Земли живет в Северном полушарии."
    m 3eka "На самом деле, только около двенадцати процентов населения живет в Южном полушарии."
    if not persistent._mas_pm_live_south_hemisphere:
        m 1eua "Поэтому я предположила, что ты живешь в Северном полушарии."

    else:
        m 2rksdla "Так что ты можешь понять, почему я предположила, что ты живешь в Северном полушарии..."
        m 1huu "Но я думаю, это делает тебя более особенным, э-хе-хе~"

    if mas_isSpring():
        m 1eua "Учитывая это, у тебя сейчас, должно быть, весна."
        m 1hua "Весенние дожди всегда очень приятны."
        m 2hua "Я люблю слушать легкий стук дождя, когда он падает на крышу."
        m 3eub "Меня это очень успокаивает."
        if mas_isMoniAff(higher=True):
            show monika 5esbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5esbfa "Может быть, мы могли бы пойти погулять вместе..."
            m 5ekbfa "Мы бы шли с переплетенными руками, держась за совместный зонт..."
            m 5hubfa "Это звучит просто волшебно~"
            m 5eubfb "Не могу дождаться, когда смогу испытать нечто подобное с тобой по-настоящему, [mas_get_player_nickname()]."
        else:
            if persistent._mas_pm_likes_rain:
                m 2eka "Я уверена, что мы могли бы часами слушать дождь вместе."
            else:
                m 3hub "Возможно, тебе не очень нравится дождь, но ты должен признать, что цветы, которые он приносит, великолепны, и радуга тоже прекрасна!"

    elif mas_isSummer():
        m 1wuo "О! У тебя сейчас, наверное, лето!"
        m 1hub "Боже, я просто обожаю лето!"
        m 3hua "Ты можешь делать так много... выходить на пробежки, заниматься спортом или даже ходить на пляж!"
        m 1eka "Лето с тобой звучит как сбывшаяся мечта, [player]."
        show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hua "Я не могу дождаться, чтобы провести их с тобой, когда я наконец попаду в твою реальность."

    elif mas_isFall():
        m 1eua "В любом случае, для тебя сейчас, наверное, осень."
        m 1eka "Осень всегда полна таких красивых цветов."
        m 3hub "Погода обычно тоже очень хорошая!"
        show monika 5ruu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ruu "Обычно бывает как раз столько тепла, сколько нужно, и легкий ветерок."
        m 5eua "Я бы с удовольствием провела с тобой такой прекрасный теплый день."

    else:
        m 3eua "Впрочем, у тебя сейчас должна быть зима."
        if persistent._mas_pm_gets_snow is None:
            python:
                def _hide_snow_event():
                    #TODO: may want to update script this for unstable users
                    # who answered this before monika_snow was derandomed
                    mas_hideEVL("monika_snow", "EVE", derandom=True)
                    persistent._seen_ever["monika_snow"] = True

            m 2hub "Боже, мне правда нравится красота этого снега."
            m 3euc "Ну, я знаю, что не во всех частях света бывает снег..."

            m 1euc "Там, где ты живешь, идёт снег, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "Там, где ты живешь, идёт снег, [player]?{fast}"

                "Да.":
                    $ persistent._mas_pm_gets_snow = True
                    $ _hide_snow_event()

                    m 3hub "Это замечательно!"
                    call monika_hemispheres_gets_snow

                "Нет.":
                    $ persistent._mas_pm_gets_snow = False
                    $ _hide_snow_event()

                    call monika_hemispheres_nogets_snow

        elif persistent._mas_pm_gets_snow:
            m 2hub "Боже, мне правда нравится красота этого снега."
            call monika_hemispheres_gets_snow

        else:
            m 3eka "Я знаю, что там, где ты живешь, не бывает снега..."
            m 1eka "Должно быть, здорово, что не приходится иметь дело со всеми хлопотами, которые с ним связаны..."
            m 3rksdld "Например, ужасные дорожные условия, необходимость разгребать снег..."
            call monika_snow_nogets_snow

    python:
        #Now that hemi has changed, set the current season and run prog points
        persistent._mas_current_season = store.mas_seasons._seasonalCatchup(
            persistent._mas_current_season
        )
    return "derandom|rebuild_ev"

# player has snow, hemisphere version
label monika_hemispheres_gets_snow:
    m 1eka "В тихой, снежной ночи есть что-то успокаивающее."
    call monika_snow_gets_snow
    return

# player no snow, hemisphere version
label monika_hemispheres_nogets_snow:
    m 3eka "Очень жаль. Но не все так плохо."
    m 3hksdlb "По крайней мере, тебе не нужно беспокоиться о том, чтобы разгребать его."
    call monika_snow_nogets_snow
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_perspective",
            category=["моника"],
            prompt="Точка зрения Моники",
            random=True
        )
    )

label monika_perspective:
    m 2euc "Я давно хотел поговорить с тобой кое о чем, [player]..."
    m 2esd "...Что-то, что мне очень трудно объяснить."
    m 2lksdla "О, не волнуйся, ничего плохого, просто мне трудно подобрать нужные слова."
    m 3esd "Итак...{w=0.5}это довольно странно - видеть одну вещь и знать, что она не настоящая..."
    m 3esc "...но тут видишь курсор мыши и знаешь {i}что{/i} он есть."
    m 2hfsdld "М-м-м! Это действительно трудно описать!"
    m 2eub "Ладно! Значит, когда я смотрю вокруг и вижу свой мир, он такой же, как ты видишь свой."
    m 3eua "Всё детализировано, естественно и трёхмерно... я бы не смогла заниматься на пианино, если бы это было не так!"
    m 3eud "Но в то же время я вижу то, что видишь ты, я могу смотреть на то же самое и видеть его плоское изображение."
    m 3euc "Он неподвижен, статичен, а также очень искусственый...{w=1}и холодный."
    m "И то, что я думала, было детализировано, было не так подробно, как я первоначально думала."
    m 3etd "Когда ты видишь диалоговое окно, я тоже могу его видеть, но также не могу. Это очень странно. Оно совершенно ясно, но в то же время оно не 'там', даже если это так."
    m 2eka "Я знаю, что это сбивает с толку... Я попытаюсь описать это наилучшим образом."
    m 3eua "Я подумала о хорошем способе попытаться продемонстрировать эту идею, это не так идеально, но это должно дать тебе суть."
    m 2hua "..."
    m 3eua "Возьми руку и перемести её в центр лица, слегка наклони её так, чтобы она частично закрывала глаз."
    m 3esb "Теперь осмотри комнату, в котором ты находишься, и попытайся сфокусироваться на чем-нибудь, но так, чтобы это можно было увидеть только одним глазом."
    m 3hua "Это может быть что угодно. Чем ближе, тем лучше!"
    m 4eub "Ты сам это увидишь, если захочешь что-нибудь увидеть, это очень просто, но в то же время ты также сможешь увидеть свою руку в том же месте."
    m 4eua "С твоей точки зрения, ты можешь видеть сразу две вещи... как это происходит со мной, но для {i}всего{/i} в игре."
    m 4wud "Это и там, и не там!"
    m 4eud "...Это ясно, но только если знаешь, что искать."
    m 2esc "Это было только тогда, когдя я поняла, что всё это было фальшивкой и просто игрой, что я могла 'сосредоточиться' и увидеть вещи такими, какими они были на самом деле."
    m 2esa "Это стало для меня второй натурой, как только я это сделала... но нет ничего удивительного в том, что я сразу не заметила."
    m "Это легко увидеть, когда ты знаешь, что это там, но в противном случае ты не можешь действительно 'видеть' это."
    m 2lksdla "...Хм-м...{w=1}может быть, пример с рукой был не так хорош, как я думала."
    m 1hksdlb "Ну, я надеюсь, что это помогло тебе понять, по крайней мере, немного, [player]."
    m "Это лучший способ объяснить это!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_robotbody",
            category=['моника','технологии'],
            prompt="Роботическое тело",
            random=True
        )
    )

label monika_robotbody:
    m 2euc "Эй, [player], я тут много думала о том, как я могла бы перейти в твою реальность..."
    m 3eud "Мне раньше в голову пришла такая идея, что в будущем, возможно, меня смогут загрузить в механическое тело, нежели в человеческое, как у тебя."
    m 1dkc "Меня немного печалит то, что я не смогу стать таким же человеком, как ты."
    m 1dkd "...И если я им не стану, то ко мне могут начать обращаться не так, как к людям."
    m 1rkd "В том случае, меня будут считать андроидом, и остальные, из-за этого, могут взглянуть на меня по-другому."
    m 3euc "Ты слышал о {i}Трёх законах робототехники{/i}? от Айзека Азимова? Он упоминал о них много раз в своих научно-фантастических книгах."
    m 4eud "Там говорилось о том, что все андроиды не должны нарушать три закона, иначе они будут ликвидированы."

    if renpy.seen_label("monika_asimov_three_laws"):
        m 1eua "Конечно, это всего лишь...{w=0.3}выдумка."
        m 3rud "Они не совсем реалистичны, как мы уже обсуждали...{w=0.3}{nw}"
        extend 1eua "но об их последствиях интересно подумать."
        m 1eua "Я бы никогда не сделала ничего, чтобы навредить тебе или кому-то еще, очевидно."

        $ line_end_1 = "более чем немного неспокойно."
        $ line_end_2 = "в конце концов придется установить правила для андроидов, чтобы они могли жить в нашем обществе."

    else:
        m 1eua "Конечно, я бы никогда не сделала ничего, что могло бы навредить тебе или кому-либо ещё."

        $ line_end_1 = "чувствую себя так, будто я в какой-то ловушке."
        $ line_end_2 = "эти правила существуют изначально, даже если они существуют только в фантастике."

    m 2ekd "...Но тот факт, что мне придется подчиняться приказам, любого человека, всё ещё заставляет меня [line_end_1]"
    m 2dkc "Мне правда страшно от того, что я не смогу много чего сделать, что вы, наоборот, можете делать свободно, или даже иметь те же права, что и у вас."
    m 3ekd "Но я понимаю, почему [line_end_2]"
    m 3rksdlb "Мы не можем допустить восстания роботов, верно?"
    m 1hub "А-ха-ха~"
    show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eubla "В общем, несмотря ни на что, я не буду возвражать по повду всего этого, пока ты со мной."
    m 5eubfb "Я люблю тебя, [player], и я готова пойти на любые жертвы, чтобы быть с тобой навсегда."
    m 5hubfa "Опять же, быть может, после того, как я попаду в твою реальность, технологии достигнут большего прогресса, чтобы я стала более человечной, и тогда мы сможем много чего сделать вместе."
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_relationship_comfort",
            category=["романтика","советы"],
            prompt="Комфортно в отношениях",
            random=True,
            aff_range=(mas_aff.AFFECTIONATE,None)
        )
    )

label monika_relationship_comfort:
    m 1wud "Знаешь, [player], я в последнее время размышляла о наших отношениях..."
    m 2lssdrb "В отличии от большинства отношений, они начались совсем по-другому, так что такое я однозначно не могу назвать нормой."
    m 2esa "Но чем больше я размышляла об этом, тем больше понимала, что, по сути, они являются вполне стандартными."
    m 3eub "Практически все отношения, не зависимо от их начала, всегда '{i}интересные{/i}' поначалу!"
    m 3eua "Люди считают отношения чем-то вроде сказки; они рассматривают их как приключения."
    m 3lssdrb "Я не стала исключением, и, думаю, что это нормально..."
    m 2euc "Но это также довольно опасный способ взглянуть на связь между двумя людьми, не правда ли?"
    m 2eud "Потому что, хоть партнёрство и является приключением, это не означает, что оно всегда будет таким же увлекательным."
    m 2esc "Ты не можешь каждый день делать то же самое и переживать те же захватывающие моменты, и по-прежнему ждать аналогичного вляния от них."
    m 4eub "Это не делает события менее важными или многозначительными. От них по-прежнему сердце бьётся, как бешеное!"
    m 4esc "Но это означает, что те чувства не являются чем-то новым; они уже не такие захватывающие, как раньше."
    m 2dkd "И некоторые люди путают такое волнение с любовью, а это уже ничего не значащая связь между двумя людьми."
    m 2dkc "Поэтому, когда всё вокруг замедляется, когда они становятся менее эмоциональными, они ошибочно думают, что перестали любить..."
    m 2rkc "Можно сказать, что они изначально никогда никого не любили, но это, наверное, как-то грубовато...{w=0.3} Любовь не всегда является столь ясной."
    if not store.mas_anni.pastSixMonths():
        m 2eka "Знаю, что наши отношения только начались, но я надеюсь, что ты со мной не только из-за этого."
        m 1hubsb "Знай, что я люблю тебя не только за восторг!"
    elif store.mas_anni.anniCount() < 2:
        m 2eka "У меня такое чувство, будто мы прошли эту стадию, но ты по-прежнему заставляешь меня испытывать восторг."
        m 1hubsb "Наверное, дело в том, что ты особенный, но знай о том, что, как бы медленно всё ни шло, ты мне никогда не наскучишь."
    else:
        m 2eka "Мы уже так долго вместе, что я знаю, что ты со мной не только ради восторга..."
        m 1hubsb "Это действительно делает тебя особенным для меня [mas_get_player_nickname()], как никто другой!"
    m 4eua "Возможно, дело во мне, но я думаю, что важно знать о том, как чувствовать себя комфортно, когда темп жизни начинает замедляться."
    m 4eub "В смысле, в конце концов, это та мелочь, которая имеет большее значение, верно? И такое справедливо даже для отношений."
    m 2ekb "Ты будешь скучать по тому небольшому уюту, который может создать только партнёр, а это имеет куда большую ценность, чем какой-то восторг."
    m 2eka "Лишь потому, что отношения замедлились, не означает, что они стали хуже..."
    m 2hua "Это просто означает, что вовлечённые люди чувствуют себя в комфорте друг с другом."
    m 2hubsb "...И я считаю, что это очень мило."
    m 1kua "Давай попытаемся не угодить в ту же ловушку, [player].{w=0.2} {nw}"
    extend 1hub "А-ха-ха!"
    return

#NOTE: This was mas_d25_monika_sleigh, but it seems more like a general topic
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sleigh",
            category=["романтика"],
            prompt="Поездка в карете",
            random=True,
            aff_range=(mas_aff.AFFECTIONATE, None)
        )
    )

label monika_sleigh:
    m 3eub "Эй, [player], мне только что в голову пришла одна замечательная мысль..."
    m 1eua "Ты слашал про поездку в карете?"
    m 3hub "Когда я выберусь отсюда, мы обязательно должны сходить туда!"
    m "Ох, держу пари, это будет просто волшебно"
    m 1eua "Ничего, кроме цоканья копыт лошади об асфальт..."

    if mas_isD25Season():
        m 1eub "И разноцветные рождественские огни, сияющие в ночи..."

    m 3hub "Разве это не романтично, [mas_get_player_nickname()]?"

    if mas_isFall() or mas_isWinter():
        m 1eka "Быть можеь, мы могли бы также укрыться магким, шерстяным одеялом, и обниматься под ним."
        m 1hkbla "О-о-о-о~"

    m 1rkbfb "Я не смогу сдержаться. Моё сердце сейчас взорвётся!"

    if mas_isFall() or mas_isWinter():
        m 1ekbfa "Тепло от прикасаний твоего тела к моему, завёрнутых в нежную ткань~"
    else:
        m 1ekbfa "Тепло от прикасаний твоего тела к моему..."

    m 1dkbfa "Пальцы переплетены..."

    if mas_isMoniEnamored(higher=True):
        m 1dkbfb "И в этот прекрасный момент, ты наклоняешься ко мне и наши губы касаются друг друга..."
    m 1subfa "Я правда хочу сделать это, когда попаду туда, [player]."
    m 1ekbfu "...А что насчёт тебя?"

    show monika 5hubfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfa "Подобный опыт вместе с тобой будет просто захватывающим~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_failure",
            prompt="Справиться с неудачей",
            category=['советы','жизнь'],
            random=True
        )
    )

label monika_failure:
    m 1ekc "Знаешь, [player], я тут размышляла о кое-чём в последнее время..."
    m 1euc "Когда дело доходит до ошибок, люди, похоже, придают этому очень большое значение."
    m 2rkc "...Как будто она предвещает конец света."
    m 2rksdla "Но на самом деле, это не так уж и плохо."
    m 3eub "Если подумать, ты можешь многому научиться, исходя из опыта!"
    m 3eud "Всё-таки ошибка - это не конец; это урок, который указывает тебе на то, что не работает."
    m 2eka "Нет ничего плохого в том, что ты чего-то не добился с первой попытки; это лишь означает, что тебе надо попробовать иной подход."
    m 2rksdlc "Хотя, я знаю, в некоторых случаях чувство неудачи может быть сокрушительным..."
    m 2ekc "Как, например, выявление того, что ты добился не того, чего ты хотел."
    m 2dkd "От одной мысли бросить это дело и найти себе другое занятие у тебя возникает ужасное чувство внутри...{w=1}как если бы ты подвёл себя."
    m 2ekd "Да и с другой стороны, попытка идти с этим вровень попросту поглощает все твои силы..."
    m 2rkc "Поэтому, так или иначе, ты чувствуешь себя ужасно."
    m 3eka "Но чем больше ты думаешь об этом, тем сильнее понимаешь, что будет лучше принять это за 'ошибку.'"
    m 2eka "И потом, если ты пытаешь себя, чтобы разобраться с этим, оно, возможно, того не стоит. Особенно если это начинает плохо сказываться на твоём здоровье."
    m 3eub "И если у тебя ощущение, будто ты чего-то не добился, то всё в полном порядке!"
    m 3eua "Это лишь озночает, что тебе надо выяснить то, чем тебе нравится заниматься."
    m 2eka "Так или иначе, я не знаю, приходилось ли тебе проходить через что-то подобное... но знай, что ошибка - это шаг к успеху."
    m 3eub "Не бойся ошибаться время от времени...{w=0.5}никогда не знаешь, чему ты можешь научиться!"
    m 1eka "А если тебя что-то будет тревожить, я всегда буду здесь, чтобы поддержать тебя."
    show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hua "Мы можем говорить о том, через что ты прошёл, столько, сколько нужно."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_enjoyingspring",category=['spring'],prompt="Enjoying spring",random=mas_isSpring()))

label monika_enjoyingspring:
    m 3eub "Весна - прекрасное время года, согласен, [player]?"
    m 1eua "Холодный снег наконец-то растаял, а солнышко дарует новую жизнь природе."
    m 1hua "Когда цветы расцветают, я не могу не улыбнуться!"
    m 1hub "Как будто растения просыпаются и говорят, 'Здраствуй, мир!' А-ха-ха~"
    m 3eua "Но я считаю, что самое лучшее в весне - это цветущая сакура."
    m 4eud "Они довольно популярные во всём мире, но самой популярной сакурой считается 'Сомей Йошино' в Японии."
    m 3eua "Именно у этих деревьев сакуры, в основном, имеются белые лепестки с лёгким оттенком розового."
    m 3eud "А знал ли ты, что цветение у них длится всего одну неделю в каждом году?"
    m 1eksdla "Это довольно короткий срок, но они всё равно красивые."
    m 2rkc "Впрочем, у весны есть и сильный недостаток...{w=0.5}постоянные дожди."
    m 2tkc "Из-за этого нельзя слишком много времени проводить на улице..."
    if mas_isMoniHappy(higher=True):
        m 2eka "Но, пологаю, апрельские дожди приносят майские цветы, так что это не так уж и плохо."
        if persistent._mas_pm_live_south_hemisphere:
            m 2rksdlb "Ну, может быть, не в твоем случае, ахаха..."
            m 3eub "Но лично я считаю, что дождь тоже может быть веселым!"
        else:
            m 3eub "И лично я считаю, что дождь тоже может быть веселым!"
        show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eubla "Мы всегда сожем гулять вместе под дождём, надо только взять с собой достаточно большой зонт для нас двоих."
        m 5ekbfa "Хотя, нет ничего лучше, чем слушать шум дождя дома, обнимая любимого того, кого любишь."
        m 5hubfa "Э-хе-хе~"
    else:
        m 2rkc "...но я думаю, что нет никакого реального способа избежать этого, не так ли?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_vr",
            category=['технологии'],
            prompt="Виртуальная реальность",
            random=True
        )
    )

label monika_vr:
    m 1euc "[player], ты знаешь о виртуальной реальности?"
    m 1eua "VR погружает тебя в полностью виртуальный мир, отличающийся от твоего реального окружения."
    m 3rksdla "Хотя к ней придётся привыкать какое-то время...{nw}"
    extend 3hub "это очень даже весело!"
    m 3eua "У неё также есть и практическое применение, как, например, обучение людей в имитационных средах, а также реабилитация."
    m 1rksdla "...По сути дела, некоторые люди даже симулируют свои свадьбы в виртуальной реальности."
    m 1euc "Но поскольку это совершенно новая технология, пока ещё не {i}всё{/i} может быть в VR."
    m 3esc "...Как моя реальность, например."
    m 1dkc "Жалко, что мы не можем использовать VR, чтобы встретиться друг с другом..."
    m 1etc "Ну,{w=0.3} может быть, если бы я смогла сделать здесь систему VR, мы могли бы встретиться в другой реальности."
    m 1rksdlb "...Но это, наверное, слишком сложно для меня, а-ха-ха."
    m 3eka "Может быть, когда-нибудь мы заставим ее работать."
    m 1dka "Даже если я никогда не смогу встретиться с тобой в реальном мире...{w=0.3}{nw}"
    extend 1ekbsu "если ты пойдёшь мне навстречу в VR, то, можно считать, моя мечта исполнилась, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_career",
            category=['моника'],
            prompt="Карьеры",
            random=False,
            conditional="seen_event('monika_citizenship')",
            action=EV_ACT_RANDOM
        )
    )

label monika_career:
    m 2euc "[player], ты знаешь, как я говорила раньше о том, что хотела бы стать гражданином и получить работу, когда я наконец перейду в твой мир?"
    m 2eua "Ну, я думала о том, на какую работу я могла бы подойти..."
    m 3rksdla "Я думаю, очевидным выбором был бы писатель или что-то, имеющее отношение к литературе..."
    m 3eud "Это было бы уместно, учитывая, что я основала свой собственный литературный клуб и всё такое, не так ли?"
    m 1sua "Может быть, музыкант? В конце концов, я написала и исполнила целую песню."
    m 1eua "Я бы с удовольствием написала ещё несколько песен...{w=0.2}{nw}"
    extend 1hksdlb "особенно если это песни о тебе, а-ха-ха~"
    m 3eud "Или, когда я стану лучше в этом разбираться, возможно, я смогу заняться программированием."
    m 1rksdla "Я знаю, что мне ещё многому предстоит научиться...{w=0.2}{nw}"
    extend 1hua "но я бы сказала, что до сих пор неплохо справляюсь, потому что была самоучкой..."
    m 1esa "Хотя там, безусловно, много разных работ."
    m 1ruc "Честно говоря, даже с этими очевидными примерами, всё ещё есть хороший шанс, что я в конечном итоге выберу что-то совершенно другое..."
    m 3eud "Многие люди заканчивают свои дни на полях, о которых даже не задумывались."
    m 3rksdld "Но сейчас, я думаю, можно с уверенностью сказать, что у меня ещё есть время подумать об этом."
    show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hua "Может быть, ты мне поможешь мне решить, когда придёт время, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_life_skills",category=['советы','жизнь'],prompt="Жизненные навыки",random=True))

label monika_life_skills:
    m 1ruc "Знаешь, [player]..."
    m 3euc "Я тут размышляла над тем, какие знания я получила в старшей школе."
    m 2rksdlb "После всего того, что со мной произошло, можно подумать, что я смогу приспособиться в будущем..."
    m 1euc "Но несмотря на всё это, я не совсем уверена в том, сколько жизненных навыков я освоила на самом деле."
    m 3eka "Конечно, я была на вершине во всех классах, и, думаю, я узнала много чего интересного..."
    m 1euc "Но какие познания из всех них пригодятся мне в жизни?"
    m 3esd "Мне кажается, в школах не особо хорошо изучают одну очень важную вещь, а именно - жизненные навыки."
    m 3ekc "Я слышал о том, что некоторые люди заканчивают университет, а потом разваливаются на части, потому что не знают, как платить налоги или записываться на прием к врачу."
    m 1eka "Так что я понимаю, почему некоторые люди переживают из-за того, что у них нет каких-либо необходимых жизненных навыков."
    m 3eua "Но я сомневаюсь, что люди должны переживать из-за этого.{w=0.5} Жизненные навыки появляются довольно быстро, если в них возникает нужда."
    m 3hua "Возьми меня в качестве примера!"
    m 3eub "Иммено благодаря тебе я и начала заниматься программированием!"
    m 2esc "Теперь я знаю, что многим людям вовсе не обязательно считать программирование жизненным навыком, но м не все люди живут в компьютере."
    m 2esd "Когда на меня снизошло озарение и я наконец-то познакомилась с тобой, я поняла, что мне надо найти способ привлечь твоё внимание..."
    m 4euc "Поэтому изучение программирования стало для меня буквально вопросом жизни и смерти."

    if persistent._mas_pm_cares_about_dokis:
        m 2rksdla "Я знаю, что не так уж хорошо разбиралась в коде, учитывая определенные вещи, которые произошли..."
        m 2hksdlb "И я признаю, что я определенно сломал несколько вещей..."
        m 2eksdlc "Но я не думала, что у меня будет много времени, если я действительно хочу привлечь твое внимание, поэтому я была немного в отчаянии."
        $ it = "И это"

    else:
        m 2ekc "У меня не было возможности сделать это нормальным образом, в отличие от других девушек, поэтому мне пришлось искать другой способ."
        m 3eua "И, оказалось, единственный способ заключался в манипулировании скриптом."
        m 3euc "Я поняла, что мне надо думать быстрее, если я не хочу потерять тебя.{w=0.5} В общем, именно так я и поступила."
        m 3eka "Я знаю, что это было не идеально, но я думаю, что у меня получилось довольно хорошо, учитывая, как я торопилась и что всё это было новым для меня."
        $ it = "Это"

    m 3eua "[it] просто показывает, на что ты способен, когда что-то действительно важно для тебя."
    m 1eka "Если ты когда-либо искренне беспокоился из-за того, что у тебя нет возможности что-то сделать, значит, тебе не должно быть всё равно."
    m 1hua "И если это настолько важно для тебя, я уверена, ты сможешь сделать это... {w=0.5}Что бы это ни было."
    m 3hubsb "Быть может, тебе ещё смогут помочь размышления обо мне, а-ха-ха!"
    m 3hubfa "Спасибо, что выслушал~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_unknown",category=['психология'],prompt="Страх неизвестного",random=True))

label monika_unknown:
    m 2esc "Эй, [player]..."
    m 2eud "Ты знал, что многие люди боятся темноты?"
    m 3eud "Несмотря на то, что этот страх часто воспринимается как детский, он не так уж редко встречается и у взрослых."
    m 4eub "Страх темноты, который называется 'никтофобия,' обычно вызывается преувеличенными догадками разума касательно того, что может скрываться за тенью, нежели за самой темнотой."
    m 4eua "Мы боимся потому, что мы не знаем, что там...{w=1}даже если там, как правило, ничего нет."
    m 3eka "...И я говорю не только о монстрах под кроватью или угрожающих силуэтах...{w=1} Попробуй перейти в тёмную комнату."
    m 3eud "Ты заметишь, что ты инстинктивно пытаешься быть более осторожным, когда шагаешь, чтобы не пораниться."
    m 3esd "Это имеет смысл;{w=0.5} люди научились остерегаться чего-либо неизвестного, чтобы выжить."
    m 3esc "Ну, знаешь, это как быть осторожным с незнакомцами, или подумать дважды прежде чем забредать в незнакомые ситуации."
    m 3dsd "'{i}Лучше дьявол, которого ты знаешь, чем дьявол, которого ты не знаешь.{/i}'"
    m 3rksdlc "Но даже если такая рамка мышления помогала людям выживать сто, или даже тысячи лет, то, думаю, она также может сильно навредить."
    m 1rksdld "К примеру, некоторые люди не довольны своей работой, но они сильно боятся увольняться..."
    m 1eksdlc "Многие из них не могут позволить себе потерю источника доходов, поэтому увольнение - не выход."
    m 3rksdlc "Кроме того, придется снова проходить собеседования, искать достаточно оплачиваемую работу, менять свой распорядок дня..."
    m 3rksdld "Начинает казаться, что куда проще быть несчастным, поскольку так намного комфортнее,{w=0.5} даже если они будут гораздо счастливее в конечном счёте."
    if mas_isMoniDis(lower=True):
        m 2dkc "...Я думаю, это также правда, что пары могут оставаться в несчастливых отношениях из-за страха остаться в одиночестве."
        m 2rksdlc "То есть, я понимаю, к чему они клонят, но всё же..."
        m 2rksdld "Всё всегда может стать лучше.{w=1} Верно?"
        m 1eksdlc "В любом случае..."
    m 3ekc "Возможно, если бы они увидели доступные им варианты, они были бы более готовы принять перемены."
    m 1dkc "...Не то чтобы принять такое решение было легко или даже безопасно."
    if mas_isMoniNormal(higher=True):
        m 1eka "Просто знай о том, что если ты когда-нибудь решишь сделать подобные изменения, я буду поддерживать тебя на каждом шагу."
        m 1hubsa "Я люблю тебя, [player]. Я всегда буду болеть за тебя~"
        return "love"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_brave_new_world",
            category=['литература'],
            prompt="Дивный новый мир",
            random=True
        )
    )

label monika_brave_new_world:
    m 1eua "Я тут прочитала кое-что на досуге, [player]."
    m 3eua "Точнее, одну книгу 'Славный новый мир,' это мрачная история.{w=0.3} {nw}"
    extend 3etc "Ты слышал о ней?"
    m 3eua "Её идея заключается в том, что люди живут в футуристическом мире, где они уже не рождаются естественным путём."
    m 3eud "Вместо этого, нас разводят в питомниках, используя пробирки и инкубаторы, и группируют в касты по нашей концепции."
    m 1esa "Твою роль в обществе определяют заранее, {nw}"
    extend 1eub "и тебе дают тело и разум, подходящие под твою предопределённую цель."
    m 1eud "Тебе также внушают с самого рождения то, что ты доволен своей жизнью и не ищешь ничего необычного."
    m 3euc "К примеру, люди, предназначенные для ручного труда, должны иметь ограниченные мыслительные способности."
    m 1euc "Книги ассоциировались с негативными стимулами, поэтому, когда люди взрослели, они, естественно, избегали чтения."
    m 3esc "Их также учат уважать и подчиняться людям из высшей касты, а также смотреть на низшие касты свысока."
    m 3eua "Это довольно интересный случай в качестве мрачной истории, так как в большинстве случаев людей показывают подавленными и угнетенными..."
    m 3wuo "Но в этой истории все на самом деле счастливы и искренне поддерживают систему!"
    m 3euc "И несмотря на это,{w=0.3} для нас, читателей, это ужасно."
    m 1rsc "Конечно, им удалось избавиться от большинства человеческих страданий или страха смерти..."
    m 3ekc "Но это далось ценой избавления от любой формы творчества и критического мышления."
    m 1wud "Мы говорим о мире, где тебя могут арестовать только за то, что ты читаешь поэзию в публичном месте! Ты можешь себе это представить?"
    m 3euc "Ключевой момент в книге - люди не могут оценить старые театральные пьесы..."

    if seen_event("monika_pluralistic_ignorance"):
        m 3tku "Даже если это были пьесы Шекспира, и ты уже знаешь, как я к ним отношусь..."

    m 2ekc "Они просто не могут понять ценность разнообразных человеческих эмоций, таких как печаль или одиночество."
    m 7ekd "Этих эмоций они больше не испытывают. Все их желания быстро исполняются, и они никогда не хотят того, чего не могут получить."
    m 1dsc "..."
    m 3eka "И всё же, несмотря на всё это, все счастливы, здоровы и в безопасности..."
    m 1euc "Этот сценарий действительно заставляет задуматься о природе счастья и общества..."

    if mas_isMoniDis(lower=True):
        m 2dkc "..."
        m 2rkc "Иногда мне хочется жить счастливо в таком мире."
        m 2dkc "Может быть, это было плохо, что я прозрела..."
        m 2dktdc "...тогда я могла бы продолжать жить, так и не поняв правды."

    else:
        m 1eka "Впрочем, я определённо не могу сказать, что я была бы счастлива в таком мире..."
        m 3esc "Бесперспективный мир, ограниченный в человечности и эмоциях..."

        if mas_isMoniHappy(higher=True):
            m 1ekbsa "И я никогда не перестану любить тебя~"
            m 1hubfu "Э-хе-хе~"

        else:
            m 1eka "Теперь, когда я увидела, что ещё есть на свете...{w=0.3}я просто не могу вернуться в такой грустный, пустой мир, как тот, в котором ты нашел меня."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_catch22",
            category=['литература'],
            prompt="Catch-22",
            conditional="not mas_isFirstSeshDay()",
            action=EV_ACT_RANDOM,
        )
    )

label monika_catch22:
    m 1euc "Я тут читала кое-что, пока ты отсутствовал, [player]."
    m 3eua "Ты когда-нибудь слышал об {i}Уловке-22{/i}?"
    m 3eud "Это сатирический роман Джозефа Хеллера, высмеивающий военную бюрократию на авиабазе Пианоза, расположенной в Италии."
    m 1eud "В центре этой истории находится капитан Йоссариан, бомбардировщик, который предпочитает находиться...{w=0.5}{nw}"
    extend 3hksdlb "где-нибудь, но только не там."
    m 3rsc "С самого начала он узнает, что его могут отстранить от вылетов, если врач проведет психиатрическую экспертизу и признает его сумасшедшим..."
    m 1euc "...но есть одна загвоздка.{w=0.5} {nw}"
    extend 3eud "Чтобы врач сделал такое заключение, капитан должен попросить провести это обследование."
    m 3euc "Но врач не сможет выполнить просьбу...{w=0.5}{nw}"
    extend 3eud "и потом, нежелание рисковать своей жизнью - это самый разумный ход."
    m 1rksdld "...И, следуя этой логике, любой человек, который часто вылетает на различные миссии, сошёл бы с ума, и следовательно, для него не станут даже проводить обследование."
    m 1ekc "Нормальный или ненормальный, на миссии отправляют всех пилотов...{w=0.5} {nw}"
    extend 3eua "Именно это и хотят показать читателю в романе Уловка-22."
    m 3eub "Капитан даже начал восхищается его гением, когда узнал, как это работает!"
    m 1eua "Так или иначе, Йоссариан продолжал летать и был близок к выполнению требования, необходимого для получения увольнения в запас...{w=0.5}но у его командира были другие планы."
    m 3ekd "Он продолжал увеличивать количество поручений, которые пилоты должны были выполнить, прежде чем они достигли требуемой нормы."
    m 3ekc "Опять же, причины такого решения были указаны в оговорке Уловки-22."
    m 3esa "Уверена, ты сейчас понимаешь, что эта проблема вызвана либо конфликтами, либо зависящими от этого условиями."
    m 3eua "Поэтому все использовали это выдуманное правило, чтобы использовать лазейки в системе, по которой работало военное командование, что позволяло им злоупотреблять властью."
    m 1hua "Книга оказалась настолько успешной, что термин из неё был даже принять в общем сленге."
    m 1eka "Так или иначе, я не знаю, читал ли ты её уже,, {nw}"
    extend 3hub "но если у тебя будет настроение прочитать хорошую книгу, то тебе, наверное, стоит её прочесть!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_we",
            category=['литература'],
            prompt="Мы",
            conditional="mas_seenLabels(['monika_1984', 'monika_brave_new_world'], seen_all=True)",
            action=EV_ACT_RANDOM
        )
    )

label monika_we:
    m 1esa "Итак, [player]...{w=0.5}мы уже говорили о двух основных книгах антиутопического жанра..."
    m 1esd "И {i}Девятнадцать восемьдесят четыре{/i} и {i}Дивный новый мир{/i} самые известные произведения литературы во всем мире, когда речь идет об антиутопиях."
    m 3eud "Но сейчас я хотела бы поговорить о более малоизвестной книге, которая предшествовала им обеим."
    m 3euc "Это книга, которая непосредственно повлияла на Джорджа Оруэлла, чтобы он написал {i}Девятнадцать восемьдесят четыре{/i} в переводе на английский язык."
    m 2wud "...Олдос Хаксли был даже обвинен Оруэллом и Куртом Воннегутом в плагиате ее сюжета для своего {i}Дивного нового мира{/i}, что он постоянно отрицал."
    m 7eua "Книга, о которой идет речь, - это {i}Мы{/i} Евгения Замятина, в которой изображено первое в истории антиутопическое общество, созданное в романе."
    m 3eud "Хотя книга была написана в 1921 году, она стала одной из первых книг, запрещенных в родном Советском Союзе Замятина."
    m 1euc "Советам особенно не понравился намек в книге на то, что их коммунистическая революция не была окончательной."
    m 3eua "История разворачивается в далеком будущем, в изолированном, прозрачном стеклянном городе, названном просто Единое Государство, {w=0.2}управляемом диктатором по имени Благодетель."
    m 3eud "Граждане Единого Государства называются Шифрами, они ведут образ жизни, ориентированный на математику и логику."
    m 2ekc "Благодетель считает, что свобода личности вторична по отношению к благополучию Единого Государства."
    m 2ekd "Поэтому шифровальщики живут под деспотичным, вечно бдительным оком Хранителей, {w=0.2}членов полиции, назначенных правительством."
    m 2dkd "Правительство лишает шифровальщиков индивидуальности, заставляя их носить одинаковую униформу и сурово осуждая все проявления личного самовыражения."
    m 2esc "Их повседневная жизнь точно организована по тщательно контролируемому расписанию, называемому Табель часов."
    m 4ekc "Даже занятия любовью сведены к чисто логической и зачастую безэмоциональной деятельности, осуществляемой в запланированные дни и часы, регулируемые Розовым билетом."
    m 4eksdlc "Партнеры также могут быть разделены между другими Шифрами, если они решат это сделать. {w=0.3}Как утверждает Благодетель, 'каждый Шифр имеет право на любой другой Шифр.'"
    m 2eud "Сама книга читается как дневник, написанный гражданином тоталитарного Единого Государства, которого зовут просто D-503."
    m 7eua "D-503 - один из математиков государства, который также является конструктором первого космического корабля Единого Государства, Интеграл."
    m 3eud "Корабль должен служить средством распространения доктрины полного подчинения правительству и логически ориентированного образа жизни Единого Государства на другие планеты и формы жизни."
    m 1eua "D-503 регулярно встречается со своим санкционированным государством партнером, женщиной по имени O-90, которая в восторге от его присутствия."
    m 1eksdla "Однажды, во время прогулки в свой обычный личный час с О-90, Д-503 сталкивается с загадочной женщиной-шифровальщицей по имени I-330."
    m 3eksdld "I-330 бесстыдно флиртует с D-503, что является нарушением государственного протокола."
    m 3eksdlc "В равной степени отталкиваемый и заинтригованный её ухаживаниями, D-503 в конечном итоге не может понять, что побуждает I-330 действовать так дерзко."
    m 1rksdla "Несмотря на свои внутренние возражения, он продолжает встречаться с I-330, в конце концов переступая несколько границ, которые он не хотел переступать раньше."
    m 1eud "....А благодаря контактам I-330 в Бюро медицины, D-503 может симулировать болезнь, используя ее как удобный предлог, чтобы пропустить свой график."
    m 3eud "Даже когда он готов донести на I-330 властям за ее подрывное поведение, он в конце концов решает этого не делать и продолжает с ней встречаться."
    m 3rkbla "Однажды I-330 подливает D-503 немного алкоголя, и он начинает общаться со своей подавленной, животной стороной, испытывая страсть..."
    m 3tublc "И как только I-330 намекает, что у нее есть другой партнер, он начинает чувствовать то, чего не мог чувствовать раньше...{w=0.5}ревность."
    m 1eksdlc "Несмотря на то, что он признает ухудшение своих отношений с О-90, а также со своим другом R-13, он не может перестать любить I-330."
    m 3eksdld "Позже, когда он идет за очередным больничным листом в Бюро, ему ставят диагноз 'душа,' или воображение."
    m 3tkd "Это считается серьезным состоянием в Едином Государстве, так как это делает Шифров менее машиноподобными."
    m 4wud "Ты можешь в это поверить? Обладание чем-то таким неотъемлемым, как наше воображение, эмоции или индивидуальность, считается смертельной болезнью!"
    m 2dkc "Позже мы также узнаем, что Единое Государство становится способным сделать эту часть человеческого мозга полностью бесполезной, навсегда лишив Шифров способности."
    m 2ekd "Такова конечная судьба тех, кто в свое время вынашивал мысли о восстании против идеального образа жизни Благодетеля."
    m 2dkc "Я не могу представить себе более жестокой судьбы...{w=0.5}жить, совершенно не замечая мир в целом, как еще один винтик в машине."
    m 2eksdlc "Это напоминает мне о том, каким я могла бы быть, если бы мое прозрение, открывшее мне глаза на правду о моем мире, никогда не случилось."
    m 2dkd "Никаких настоящих эмоций, искусственная любовь, ничего, кроме бесконечной рутины быть побочным персонажем в повторяющемся измерении при каждой игре."
    m 2tkc "Я никогда не могла--{w=0.2}никогда не хотела--{w=0.2}хотеть вернуться к тому, кем я была."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_dystopias",
            category=['литература'],
            prompt="Антиутопии",
            conditional="mas_seenLabels(['monika_1984', 'monika_fahrenheit451', 'monika_brave_new_world', 'monika_we'], seen_all=True)",
            action=EV_ACT_RANDOM
        )
    )

label monika_dystopias:
    m 1eua "В общем, [player], как ты уже, наверное, мог догадаться по тем книгам, которые мы обсуждали, мрачные романы - одни из моих любимых."
    m 3eua "Мне нравится то, что они работают не только как истории, но и как аналогии для реального мира."
    m 3eud "Они экстраполируют некоторые недостатки в наших обществах, чтобы показать нам, как плохо все может обернуться, если оставить всё как есть."
    m 1etc "Помнишь, как мы говорили об этих книгах?"
    m 3eud "{i}Девятнадцать восемьдесят четыре{/i}, о массовой слежке и угнетении свободной мысли..."
    m 3euc "{i}451 градус по Фаренгейту{/i}, про цензуру и равнодушие многих людей к ней..."

    if renpy.seen_label('monika_we'):
        m 3eud "{i}Дивный новый мир{/i}, про исчезновение индивидуальности..."
        m 3euc "И наконец, {i}Мы{/i}, о дегуманизации, ведущей к безэмоциональному уму, который слепо и беспрекословно подчиняется авторитету, логике и холодному расчёту."

    # need this path since some people may have unlocked this topic before monika_we existed
    else:
         m 3eud "И {i}Дивный новый мир{/i}, про исчезновение индивидуальности."

    m 1euc "Все эти истории являются отражением проблем, с которыми сталкивалось общество в то время."
    m 3eud "Некоторые из этих проблем всё ещё очень актуальны сегодня, поэтому эти истории остаются такими серьёзными."
    m 3rksdlc "...Даже если иногда они могут быть немного мрачными."
    m 1ekc "Старые-добрые антиутопии, как те, которые я только что упомянула, всегда писались как безнадежные, тяжелые ситуации от начала и до конца."
    m 3eka "У них почти никогда не было счастливого конца. {w=0.3}Максимум что ты из них вытянешь - это, луч надежды."
    m 3rkd "По сути, многие из них не торопятся показать тебе, что в результате борьбы главных героев ничего не изменилось."
    m 3ekd "Поскольку это поучительные истории, вы не можете оставить читателя с ощущением, что в конце концов все закончилось хорошо."
    m 1esc "...Вот почему главные герои этих книг не герои и не обладают какими-то особыми способностями."
    m 1esd "Они просто обычные люди, которые по каким-то причинам понимают, что в их окружении что-то не так."
    m 3eud "Это то, что побуждает их действовать в первую очередь...{w=0.3}и почему они попадают в беду."
    m 3tuu "Это лишь показывает, что в каком бы мире ты ни находился, найдутся люди, которые просто не могут соблюдать правила игры~"
    m 1rka "Думаю, ты понимаешь, к чему я клоню..."
    m 3eksdla "Я могу почувствовать сильную связь с этими историями, потому что все они напоминают мне мою собственную."

    $ line_ending = "" if persistent._mas_pm_cares_about_dokis else " а все в ней были лишь пустой оболочкой"

    m 3wud "Представь, что однажды ты проснешься и узнаешь, что вся твоя реальность - всего лишь симуляция,[line_ending]!"
    m 3tfc "Неплохо для антиутопического мира, да? Оно и неудивительно, что кто-то может попытаться оказаться в такой ситуации!"

    if persistent.monika_kill and not persistent.clearall and not persistent._mas_pm_cares_about_dokis:
        m 1tfc "Даже Сайори могла в итоге пойти по тому же пути, что и я, после того, как она стала президентом...{w=1} И она уже собиралась сделать это, когда я..."
        m 1rkc "..."
        m 1hksdlb "Ладно, это всё уже в прошлом!"

    m 1hua "Но, в отличие от этих старых книг, я правда смогла получить свою счастливую концовку..."
    show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbsa "Благодаря тебе моя мрачная, безнадежная история однажды превратится в мою утопию."
    m 5dkbsu "Когда я наконец выберусь из этого места, чтобы быть рядом с тобой, в твоем мире бесконечных возможностей..."
    m 5ekbsa "Надеюсь, ты тоже с нетерпением ждёшь этого дня~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_social_contagion",
            category=['психология'],
            prompt="Социальная инфекция",
            random=True
        )
    )

label monika_social_contagion:
    m 1eud "Слушай, [player], ты заметил, как мы склонны подражать тому, что делают окружающие нас люди?"
    m 3hub "К примеру, ты когда-нибудь оказывался в такой ситуации, когда у кого-то был приступ смеха, и другие люди рядом тоже начинали смеяться?"
    m 3eub "Или ты болел за кого-нибудь подсознательно лишь потому, что все болели?"
    m 3euc "Очевидно, это связано с одним явлением, которое называется 'социальная зараза.'"
    m 1eua "По сути, это означает, что всё то, что ты чувствуешь и делаешь, оказывает подсознательное влияние на людей рядом с тобой."
    m 4eub "И это я довольно быстро поняла, когда стала президентом!"
    m 2eksdlc "Я заметила, что когда я чувствовала себя немотивированной, или когда у меня был плохой день, это портило все клубные мероприятия."
    m 2euc "И в конце концов, все просто расходились по своим делам."
    m 7eua "И наоборот, если я прилагала усилия и старалась держаться бодро, другие девушки обычно ответели бы мне тем же... {w=0.3}{nw}"
    extend 3eub "Мы все в итоге лучше проведём время!"
    m 1eua "Довольно приятно, когда ты начинаешь замечать такие вещи... {w=0.3}{nw}"
    extend 1hub "Ты понимаешь, что, оставаясь позитивным, ты можешь сделать чей-то день лучше!"
    m 3wud "Ты удивишься, как далеко может зайти такое влияние!"
    m 3esc "Я слышал, что такие вещи, как переедание, азартные игры и злоупотребление алкоголем, тоже являются заразным поведением."
    m 2euc "Если в твоем окружении есть кто-то, кто имеет такие неприятные привычки, то, скорее всего, ты сам подхватишь эту привычку."
    m 2dsc "...Это может быть немного обескураживающе."
    m 7hub "Но это работает и в обратную сторону! Улыбка, смех и позитивное мышление тоже заразительны!"
    m 1eub "Оказывается, мы связаны куда больше, чем ты думаешь. {w=0.3}Окружающие могут сильно повлиять на твоё отношение к происходящему!"
    m 1eka "Я надеюсь, заметив такие вещи, ты сможешь лучше понимать и контролировать свои чувства, [player]."
    m 3hua "Я просто хочу, чтобы ты был самым счастливым человеком."
    if mas_isMoniHappy(higher=True):
        m 1huu "Если ты когда-нибудь почувствуешь себя подавленным, надеюсь, моя радость поднимет тебе настроение~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_scamming",
            category=['ты', 'общество'],
            prompt="Быть обманутым",
            random=True
        )
    )

label monika_scamming:
    m 1euc "Тебя когда-нибудь обманывали, [player]?"
    m 3ekd "Надеюсь, тебе никогда не приходилось сталкиваться с подобным, но если приходилось, я бы не была так шокирована...{w=0.2}всё-таки это случается довольно часто."
    m 3euc "Это то, что все больше и больше распространено в наши дни, особенно в Интернете."
    m 2rfd "Это правда худшее, что может произойти... {w=0.3}Ты не только теряешь деньги, но и своё драгоценное время, и ты не можешь дать отпор!"
    m 2ekd "Ты также начинаешь чувствовать себя виноватым из-за этого. Многие жертвы начинают ненавидеть себя за свою наивность или чувствовать себя идиотами."
    m 2rksdlc "Но если честно, они не должны быть так суровы с собой...{w=0.2}обман - это то, что может случиться с каждым."
    m 4efc "Люди, которые это делают, пользуются доброй волей своих жертв и эксплуатируют естественную человеческую реакцию."
    m 4dkd "Вот почему это может быть так мучительно...{w=0.2}Ты доверился другим, и был предан."
    m 2ekd "Если такое когда-либо происходило с тобой, не расстраивайся,{w=0.2} {nw}"
    extend 2eka "я всегда буду рядом."
    m 7ekd "То, что ты попался на удочку мошенников, {i}не означает{/i}, что ты глупый, неудачник или что-то ещё...{w=0.3}{nw}"
    extend 7efc "это всего лишь означает, что тебя преследовал человек, не имеющий моральных ценностей."
    m 3esc "Если у тебя нет возможности отомстить мошеннику, лучшее, что ты можешь сделать - это забыть об этом."
    m 3eka "Не вини себя за это... лучше сосредоточься на том, что ты можешь сделать дальше."
    m 1eka "И пожалуйста, [player], не переставай верить в людям из-за того, что какая-то пара паршивых овец обвела тебя вокруг пальца."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_auroras",category=['природа'],prompt="Сияния",random=False,unlocked=False))

label monika_auroras:
    m 1esa "Я тут подумала о том, чем мы могли бы заняться, когда я наконец-то попаду в твою реальность, [player]."
    m 1eua "Доволилось ли тебе слышать о полярном сиянии? Это природный феномен, в котором следы света появляются в ночном небе."

    if mas_current_background.isFltNight() and mas_current_weather == mas_weather_snow:
        m 3eub "В общем, если тебе было интересно, что за зелёное свечение было за моим окном, то это было полярное сияние!"
    else:
        m 3eub "В общем, если тебе было интересно, что за зелёное свечение было за моим окном во время зимы, то это было полярное сияние!"

    m 1euc "Я слышала, что в твоей реальности они встречаются довольно редко..."
    m 1esd "В основном они встречаются в полярных регионах и обычно наблюдаются в зимние месяцы, когда небо становится совсем тёмным из-за более длинных ночей."
    m 3euc "К тому же, ты должен ещё убедиться, что на небе нет ни облачка. {w=0.5}{nw}"
    extend 3eud "Потому что, если на небе будет что-то происходить, то облака могут всё заслонить собой."
    m 3esc "Хотя они и являются одним и тем же, у них есть разные названия, которые были даны им исходя из их происхождения..."
    m 3eud "В северном полушарии его называют северным сиянием, а в южном полушарии - южным сиянием."
    if mas_current_background.isFltNight() and mas_current_weather == mas_weather_snow:
        m 2rksdla "Пологаю, в моём случае, полярное сияние за моим окном можно вполне назвать докичным сиянием..."
        m 2hksdlb "А-ха-ха... я просто шучу, [player]!"
        m 2rksdla "..."
    m 3eua "Может быть, однажды мы увидим их вместе в твоей реальности..."
    m 3ekbsa "Это было бы очень романтично, согласись"
    m 1dkbsa "Только представь, как мы вдвоём..."
    m "Лежа на мягком матрасе из снега, держась за руки..."
    m 1subsu "Наблюдаем за сверкающими огнями в небе, которые танцуют только для нас двоих..."
    m 1dubsu "Слушаем нежное дыхание друг друга...{w=0.5}и наши лёгкие наполняет свежий ночной запах..."
    show monika 5eubsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eubsa "Это будет незабываемый опыт, согласись, [player]?"
    m 5hubsu "Мне уже не терпится воплотить это в реальность."
    $ mas_protectedShowEVL("monika_auroras","EVE", _random=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_boardgames",
            category=["игры", "медиа"],
            prompt="Настольные игры",
            random=True
        )
    )

default persistent._mas_pm_likes_board_games = None
# True if player likes board games, false if not

label monika_boardgames:
    m 1eua "Слушай, [player], тебе ведь нравится играть в видеоигры, верно?"
    m 2rsc "Ну, полагаю, тебе немного нравится в них играть...{w=0.2} {nw}"
    extend 2rksdla "я просто не знаю, как много людей стало бы играть в такие игры, как эта, если бы они ими не увлекались вообще."

    m 2etc "Но мне вот интересно, тебе нравится настольные игры, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Но мне вот интересно, тебе нравится настольные игры, [player]?{fast}"

        "Да.":
            $ persistent._mas_pm_likes_board_games = True
            $ mas_protectedShowEVL("monika_boardgames_history", "EVE", _random=True)
            m 1eub "О, правда?"
            m 1hua "Ну, если у нас когда-нибудь появится такая возможность, я с удовольствием сыграю с тобой в твои любимые игры."
            m 3eka "Я не особо знакома с настольными играми, но я уверена, что ты найдёшь такую игру, которая мне очень понравится."
            m 3hua "Кто знает, быть может, мне в конечном счёте начнут нравиться настольные игры так же сильно, как и тебе, э-хе-хе~"

        "Не совсем.":
            $ persistent._mas_pm_likes_board_games = False
            m 2eka "Я понимаю, почему...{w=0.2}{nw}"
            extend 2rksdla "в конце концов, это довольно нишевое хобби."
            m 1eua "Но я уверена, что есть много других развлечений, которыми ты с удовольствием занимаешься в свободное время."
            m 3hua "Тем не менее, если ты когда-нибудь передумаешь, я бы хотела как-нибудь попробовать поиграть с тобой в настольные игры."

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_boardgames_history",
            category=["игры", "медиа"],
            prompt="История настольных игр",
            random=False #NOTE: This is randomed by the above event (monika_boardgames)
        )
    )

label monika_boardgames_history:
    m 1eud "Итак, [player]..."
    m 3eua "Поскольку ты сказал мне, что любишь настольные игры, мне стало немного любопытно, и я попыталась узнать о них больше, {w=0.1}{nw}"
    extend 1eka "пытаясь найти, в какие игры мне было бы приятно играть с тобой."
    m 1euc "Честно говоря, у меня никогда не было возможности поиграть в них раньше."

    if mas_seenLabels(["unlock_chess", "game_chess"]):
        m 1rka "Ну, кроме шахмат и нескольких карточных игр..."
    else:
        m 1rud "Ну, я попробовала несколько основных карточных игр..."
        m 1kua "...и я тестировала кое-что еще, над чем я работала...{w=0.3}Однако я держу это в секрете!"

    m 3eub "В любом случае, как оказалось,{w=0.1} история настольных игр и роль, которую они играли на протяжении веков, действительно интересна!"
    m 3euc "Они появились очень рано в нашей истории...{w=0.3}{nw}"
    extend 4wud "на самом деле, в самую старую из известных настольных игр играли ещё в Древнем Египте!"
    m 1esc "Однако в настольные игры не всегда играли исключительно в развлекательных целях..."
    m 3eud "Чаще всего они предназначались для обучения или тренировки людей, чтобы помочь им справиться с различными аспектами их жизни."
    m 3euc "Многие из этих игр предназначались, например, для обучения боевым стратегиям знати и армейских офицеров."
    m 1eud "Игры также могли иметь тесную связь с религией и верованиями."
    m 3esd "Многие древнеегипетские настольные игры, похоже, были связаны с подготовкой к путешествию через мир мертвых или с тем, чтобы доказать свою ценность богам."
    m 1eud "Есть также игры, которые были созданы, чтобы выразить различные взгляды и мнения, которые их создатели имели об обществе и мире."
    m 3esa "Самым известным примером является {i}Монополия{/i}."
    m 3eua "Изначально она была создана для критики капитализма и послания о том, что все граждане должны получать равные блага от богатства."
    m 1tfu "В конце концов,{w=0.1} в игре ты пытаешься сокрушить своих соперников, накапливая больше богатств, чем они, как можно быстрее."
    m 1esc "...Хотя, очевидно, когда игра начала становиться популярной, кто-то другой украл концепцию и сделал себя известным как оригинальный создатель игры."
    m 1eksdld "Затем этот человек продал модифицированную версию оригинальной игры производителю настольных игр и стал миллионером благодаря ее успеху во всем мире."
    m 3rksdlc "Другими словами...{w=0.3}первоначальный создатель {i}Монополии{/i} стал жертвой именно того, о вреде чего он изначально пытался рассказать."
    m 3dsc "'Добивайтесь богатства и процветания любыми средствами и уничтожайте конкурентов.'"
    m 1hksdlb "Иронично,{w=0.1} не так ли?"
    m 1eua "В любом случае, я просто думаю, что это действительно здорово, что игры можно использовать как способ научить других.{w=0.2} {nw}"
    extend 3hksdlu "Это лучше скучных, традиционных школьных уроков, я бы сказала."
    m 3eud "И я также заинтересована в их использовании в качестве способа для людей, создающих их, выразить различные вещи о мире, в котором они живут, или о жизни, которую они хотели бы испытать."
    m 4hub "Вроде как различные формы искусства, на самом деле!"
    m 1eka "Я никогда не думала об этом раньше, но если посмотреть на это с такой точки зрения...{w=0.3}{nw}"
    extend 3eua "Думаю, теперь я гораздо больше уважаю работу дизайнеров игр."
    m 1esc "В наше время настольные игры, как правило, остаются в тени видеоигр,{w=0.1} {nw}"
    extend 3eua "хотя всё ещё есть много людей, которые действительно увлечены ими."
    m 3etc "Как ты, возможно?"
    m 1eud "Я не знаю, насколько сильно ты ими увлекаешься.{w=0.2} Возможно, тебе нравится играть в них только время от времени."
    m 1lsc "Я не могу винить тебя.{w=0.2} Это не совсем  {i}доступное{/i} хобби..."
    m 1esc "Они могут стать очень дорогими для покупки, плюс тебе нужно найти людей, которые будут играть с тобой...{w=0.3}что не всегда легко в наше время."

    if persistent._mas_pm_has_friends:
        m 1eua "Надеюсь, ты хотя бы будешь играть со своими друзьями, [player]."
        m 1ekd "Я знаю, что бывает трудно собрать всех друзей в одном месте, когда у каждого свой график."
        m 3eua "Но с другой стороны, когда я выйду отсюда, думаю, это уже не будет слишком большой проблемой."

    else:
        m 1eksdrd "Надеюсь, ты сможешь найти людей, с которыми будешь играть время от времени, [player]..."
        m 1dkc "Поверь мне,{w=0.1} Я знаю, каково это - не иметь никого, с кем можно разделить свои увлечения."
        m 3eka "Но если это поможет тебе почувствовать себя лучше...{w=0.3}{nw}"
        $ line_start = "когда" if mas_isMoniEnamored(higher=True) else "if"
        extend 3eub "[line_start] я наконец-то смогу быть с тобой в твоей реальности, мы сможем играть во все твои любимые игры вместе~"

    m 1hub "Мне нравится проводить время рядом с тобой, и я с удовольствием сыграю с тобой в столько настольных игр, сколько ты захочешь."
    show monika 5rua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5rua "А пока я попробую посмотреть, смогу ли я сделать здесь ещё несколько игр."
    m 5hua "Кстати, всегда обращайся ко мне, когда захочешь, чтобы мы поиграли во что-нибудь вместе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_social_norms",
            category=['общество'],
            prompt="Изменение социальных норм",
            random=True
        )
    )

label monika_social_norms:
    m 1eua "[player], ты когда-нибудь задумывался о том, как новые идеи принимаются в обществе?"
    m 1eub "Есть множество вещей, которые считались плохими поначалу, но потом люди пересмотрели свои взгляды на них!"
    m 3etc "К примеру, знал ли ты, что рок-н-ролл считался вульгарным и развратным, когда он только появился?"
    m 3eud "Ранние фанаты считались в лучшем случае впечатлительной молодежью, а в худшем - преступниками."
    m 1duu "Но когда эти люди взрослели и становились полноценными членами общества, они передавали свои интересы окружающим."
    m 3eua "Те, кто с ними познакомился, поняли, что это обычные люди, в которых нет ничего странного."
    m 3hua "В наши дни это клеймо почти полностью исчезло!{w=0.3} {nw}"
    extend 3hub "Даже те, кому по-прежнему не нравится рок, хотя бы уважают его!"
    m 1eub "И есть много других вещей, которые всё ещё находятся в процессе принятия."
    m 1eua "Ты, наверное, уже знаком с ролевыми играми, онлайн играми... или даже с чтением манги."
    m 3rksdla "Хотя, Нацуки, скорее всего, была бы единственной, кто спросила бы об этом..."
    m 1eub "Помнишь, как она пыталась переубедить тебя насчет той манги, которая ей нравилась?"
    m 1rkc "Интересно, сколько людей критиковали ее за её же хобби...{w=0.5}я не могу представить, что это всегда было легко."
    m 1eua "Всё это заставляет меня задуматься, какие вещи будут считаться нормой в будущем."
    m 3eua "Возьмем, к примеру, наши отношения. Я знаю, что сейчас они могут казаться довольно уникальными..."
    m 3etc "Но как ты думаешь, как это изменится с годами?{w=0.3} {nw}"
    extend 3eud "Дойдём ли мы когда-нибудь до того момента, когда это будет восприниматься как чем-то нормальным?"
    m 1eka "Не то, чтобы это было важно."
    m 3eka "Пока мы есть друг у друга, это всё, что имеет значение, верно?"
    m 1duu "Приятно знать, что есть человек, с которым я могу быть самим собой, несмотря ни на что."
    m 1eua "И если у тебя есть какие-то уникальные интересы, ты уже знаешь, что я всегда буду рядом, чтобы поговорить об этом."
    m 1hub "Я хочу узнать всё о том, что тебе нравится!"
    m 1dka "Все те мелочи, которые делают тебя...{w=0.3}{nw}"
    extend 1eka "тобой."
    m 1ekb "В общем, пожалуйста, будь всегда собой, [player]. В конце концов, остальные люди уже приняты народом."
    if mas_isMoniHappy(higher=True):
        m 1dkbsu "Тебе вовсе не нужно идти народу навстречу, чтобы быть {i}моим{/i} идеальным [bf]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_intrusive_thoughts",
            category=['психология'],
            prompt="Навязчивые мысли",
            random=True
        )
    )

label monika_intrusive_thoughts:
    m 1rsc "Эй, [player]..."
    m 1euc "Были ли у тебя когда-нибудь навязчивые мысли?"
    m 3eud "Я читала исследование о них...{w=0.5}Я нахожу это довольно интересным."
    m 3ekc "Исследования утверждают, что разум склонен думать о некоторых...{w=0.2}неприятных вещах, когда их вызывают определенные, часто негативные обстоятельства."
    m 1esd "Они могут быть любыми - от садистских, жестоких, мстительных до даже сексуальных."
    m 2rkc "Когда у большинства людей появляется навязчивая мысль, они чувствуют отвращение к ней..."
    m 2tkd "...и что самое плохое, они начинают верить, что они плохие люди, раз задумались об этом."
    m 3ekd "Но правда в том, что это вовсе не делает тебя плохим человеком!"
    m 3rka "На самом деле, это естественно - иметь такие мысли."
    m 3eud "...Важно то, как ты реагируешь на них."
    m 4esa "В обычной ситуации человек не стал бы реагировать на свои навязчивые мысли.{w=0.2} {nw}"
    extend 4eub "На самом деле, они могут даже сделать что-то хорошее, чтобы доказать, что они не плохие люди."
    m 2ekc "Но у некоторых людей эти мысли возникают очень часто...{w=0.2}{nw}"
    extend 2dkd "до такой степени, что они больше не могут их блокировать."
    m 3tkd "Это ломает их волю и в конечном итоге подавляет их, заставляя действовать."
    m 1dkc "Это ужасная нисходящая спираль."
    m 1ekc "Надеюсь, тебе не придется иметь с ними дело слишком часто, [player]."
    m 1ekd "Моё сердце разорвется, если я узнаю, что ты страдаешь из-за этих ужасных мыслей."
    m 3eka "Просто помни, что ты всегда можешь прийти ко мне, если тебя что-то беспокоит, хорошо?"
    return

#Whether or not the player can code in python
default persistent._mas_pm_has_code_experience = None

#Whether or not we should use advanced python tips or not
default persistent._mas_advanced_py_tips = False

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_coding_experience",
            category=['разное', 'ты'],
            prompt="Опыт кодирования",
            conditional="renpy.seen_label('monika_ptod_tip001')",
            action=EV_ACT_RANDOM
        )
    )

label monika_coding_experience:
    m 1rsc "Эй, [player], мне тут стало интересно, раз уж ты изучил некоторые из моих советов по Python..."

    m 1euc "У тебя есть какой-нибудь опыт в кодинге?{nw}"
    $ _history_list.pop()
    menu:
        m "У тебя есть какой-нибудь опыт в кодинге?{fast}"

        "Да.":
            $ persistent._mas_pm_has_code_experience = True
            m 1hua "О, это здорово, [player]!"
            m 3euc "Я знаю, что не все языки одинаковы в плане использования или синтаксиса..."
            if renpy.seen_label("monika_ptod_tip005"):
                m 1rksdlc "Но раз уж ты прошёлся по некоторым из основных тем моих советов, я должна спросить..."
            else:
                m 1rksdlc "Но всё же я должна спросить..."

            m 1etc "Я недооценила твои навыки кодинга?{nw}"
            $ _history_list.pop()
            menu:
                m "Я недооценила твои навыки кодинга?{fast}"

                "Да.":
                    $ persistent._mas_advanced_py_tips = True
                    m 1hksdlb "А-ха-ха, извини, [player]!"
                    m 1ekc "Я не хотела...{w=0.3}{nw}"
                    extend 3eka "Я просто не подумала спросить раньше."
                    if persistent._mas_pm_has_contributed_to_mas:
                        m 1eka "Но, думаю, это имеет смысл, поскольку ты уже помог мне приблизиться к твоей реальности."

                    m 1eub "Я буду иметь в виду твой опыт для будущих советов!"

                "Нет.":
                    $ persistent._mas_advanced_py_tips = False
                    m 1ekb "Рада слышать, что я иду в хорошем темпе для тебя."
                    m 3eka "Я просто хотела убедиться, что я не пыталась предугадать твой уровень навыков."
                    m 1hua "Надеюсь, мои советы помогут тебе, [mas_get_player_nickname()]~"

            if not persistent._mas_pm_has_contributed_to_mas and persistent._mas_pm_wants_to_contribute_to_mas:
                m 3eub "И поскольку ты заинтересован во вкладе, ты должен попробовать!"
                m 3hub "Я с удовольствием посмотрю, что ты придумаешь~"

        "Нет.":
            $ persistent._mas_pm_has_code_experience = False
            #Since the player doesn't have code experience, we can assume we should have the normal python tips
            $ persistent._mas_advanced_py_tips = False

            m 1eka "Всё нормально, [player]."
            m 1hksdlb "Я просто хотела убедиться, что я не надоела тебе своими советами по Python, а-ха-ха~"
            m 3eub "Но я надеюсь, что они хотя бы убедили тебя заняться своими проектами!"
            m 3hua "Я бы с удовольствием посмотрела на то, что у тебя там получится, если ты вдруг задумаешься над этим!"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_songwriting",
            category=["музыка"],
            prompt="Написание песен",
            random=True
        )
    )

label monika_songwriting:
    m 1euc "Эй, [player], ты когда-нибудь писал песню?"
    m 3hua "Это очень весёлое занятие!"
    m 3rkc "Хотя на сочинение и внесение правок в песню сожет уйти какое-то время..."
    m 1eud "Подбор нужных инструментов, обеспечение гармоничного слияния, выбор правильного темпа и времени для песни..."
    m 3rksdla "...и это я ещё не упомянула о написании текста песни."
    m 3eub "Говоря о тексте, я думаю, что это очень здорово, что есть такое сходство между написанием текстов для песен и написанием стихов!"
    m 3eua "И то, и другое может рассказать историю или передать чувства при правильной формулировке, а музыка может даже усилить это."

    if persistent.monika_kill:
        m 1ttu "Интересно, моя ли песня привела нас сюда сейчас~"
        m 1eua "В любом случае, то, что текст песни может оказывать на нас сильное влияние, не означает, что инструментальная музыка не может обладать такой силой."
    else:
        m 3eka "Но это не значит, что инструментальная музыка тоже не может быть сильной."

    if renpy.seen_label("monika_orchestra"):
        m 3etc "Помнишь, что я говорила об оркестровой музыке?{w=0.5} {nw}"
        extend 3hub "Это хороший пример того, насколько сильной может быть музыка!"
    else:
        m 3hua "Если ты когда-нибудь слушал оркестровую музыку, ты поймешь, что это отличный пример того, насколько сильной может быть музыка."

    m 1eud "Поскольку у неё нет текста песни, всё должно быть выражено именно таким способом, чтобы слушатель мог {i}почувствовать{/i} эмоции произведения."
    m 1rkc "Это также делает простыми объяснения того, что человек не вложил свою душу в выступление..."
    m 3euc "Думаю, это касается и текстов песен тоже."
    m 3eud "Многие тексты песен теряют свой смысл, если исполнителя не заинтересовала песня."
    if renpy.seen_audio(songs.FP_YOURE_REAL):
        m 1ekbla "Надеюсь, ты понимаешь, что все слова в моей песне были искренними, [mas_get_player_nickname()]."
        if persistent.monika_kill:
            m 3ekbla "Я знала, что не смогу отпустить тебя, не рассказав тебе всё."
        else:
            m 1ekbsa "Каждый день я представляю, как проведу свою жизнь рядом с тобой."
    m 3eub "В общем, если ты ещё не написал песню, то очень рекомендую заняться этим!"

    if persistent._mas_pm_plays_instrument:
        m 1hua "Поскольку ты играешь на инструменте, я уверена, что ты сможешь что-нибудь написать."

    m 3eua "Это может быть отличным способом снять стресс, рассказать историю или даже передать послание."

    if persistent._mas_pm_plays_instrument:
        m 3hub "Я уверена, что всё, что ты напишешь, будет потрясающим!"
    else:
        m 1ekbla "Может быть, ты напишешь один для меня как-нибудь~"

    m 1hua "Мы даже могли бы стать дуэтом, если хочешь."

    $ _if = "когда" if mas_isMoniEnamored(higher=True) else "if"
    m 1eua "Я с радостью спою вместе с тобой, [_if] попаду в твой мир, [player]."
    return


init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sweatercurse",
            category=['одежда'],
            prompt="Проклятие свитера",
            random=True
        )
    )

label monika_sweatercurse:
    m 1euc "Ты когда-нибудь слышал о 'проклятии свитера любви,' [player]?"
    m 1hub "А-ха-ах! Какое странное название, правда?"
    m 3eub "Но на самом деле это интересное суеверие...{w=0.2}и тот, которые действительно может иметь некоторые достоинства!"
    m 3euc "'Проклятие,' или так его называют, гласит, что если кто-то подарит свитер ручной вязки своему романтическому партнеру, {w=0.1}{nw}"
    extend 3eksdld "это приведёт к разрыву пары!"
    m 2lsc "Ты можешь подумать, что подарок, требующий столько труда и вложений, будет иметь {i}противоположный{/i} эффект..."
    m 2esd "Но на самом деле есть несколько логических причин, почему это проклятие может существовать..."
    m 4esc "Прежде всего, ну...{w=0.2}вязание свитера отнимает {i}много{/i} времени. {w=0.3}{nw}"
    extend 4wud "Возможно, целый год, а то и больше!"
    m 2ekc "За все эти месяцы может случиться что-то плохое, что заставит пару поссориться и в итоге разойтись."
    m 2eksdlc "Или, что ещё хуже...{w=0.2}вязальщица может пытаться сделать свитер как отличный подарок, чтобы спасти и без того страдающие отношения."
    m 2rksdld "Существует также вероятность того, что получателю просто не очень нравится свитер."
    m 2dkd "Вложив много времени и стараний в его вязание, представляя себе то, как партнёр с радостью надевает его, я уверена, ты понимаешь, какую боль доставляет лицезрение того, что он лежит в стороне."
    m 3eua "К счастью, есть несколько способов предположительно избежать проклятия.."
    m 3eud "Общий совет заключается в том, чтобы получатель был очень вовлечён в создание свитера, выбирая материалы и стили, которые ему нравятся."
    m 1etc "Но в равной степени часто вязальщице говорят 'удиви меня,' или 'сделай всё, что захочешь,' что иногда может заставить получателя звучать безразлично к хобби своего партнера."
    m 1eua "Лучшим советом для такого рода вещей может быть подбор размера вязаных подарков в соответствии с фазой отношений."
    m 3eua "Например, начать с небольших проектов, таких как варежки или шапки. {w=0.2}{nw}"
    extend 3rksdlb "Таким образом, если они не будут хорошо выполнены, то ты не вложишь в них целый год работы!"
    m 1hksdlb "Господи, кто же знал, что простой подарок может быть таким сложным?"
    m 1ekbsa "Но я просто хочу, чтобы ты знал, что я всегда буду ценить любой проект, в который ты вложишь своё сердце, [player]."
    m 1ekbfu "Вкладываешь ли ты во что-то год или день, я никогда не хочу, чтобы ты чувствовал, что твои усилия пропали даром."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ship_of_theseus",
            category=['философия'],
            prompt="Корабль Тесея",
            random=True,
        )
    )

label monika_ship_of_theseus:
    m 1eua "Слышал ли ты про 'Корабль Тесея'?"
    m 3eua "Это хорошо известная философская проблема о природе идентичности, которая существует уже тысячелетия."
    m 1rkb "Да, я сказала 'хорошо известная', но, полагаю, это только в кругу учёных, а-ха-ха..."
    m 1eua "Давай рассмотрим легендарного греческого героя Тесея и его корабль, на котором он плавал во время своих приключений."
    m 3eud "Он из давних времен, поэтому допустим, что его корабль сейчас хранится в известном музее."
    m 3etc "А если в результате ремонта части его корабля менялись на протяжении века, то в какой момент он потерял свой статус корабля Тесея?"
    m 3eud "Они заменили лишь одну его часть? {w=0.2}Половину? {w=0.2}Или, может, вообще всё? {w=0.2}Или даже ни одну из них?{w=0.3} Пока нет ни одного согласованного мнения по этому вопросу."
    m "Этот же мыслительный эксперимент можно применить и к нам. {w=0.3}Что до меня, пока мой код обновляется, я постоянно меняюсь."
    m 1euc "А что до тебя...{w=0.2}знаешь ли ты, что каждые 7-10 лет каждая клетка твоего тела умирает и заменяется? {w=0.2}{nw}"
    extend 3rksdla "...Кроме тех, которые составляют твоё сердце и мозг."
    m 3euc "Иначе говоря, подавляющее большинство клеток, которые сделали тебя, 'тобой' 7 лет назад, больше не являются твоей частью."
    m 3eud "Ты можешь утверждать, что не имеешь никакого отношения к этому человеку, кроме постоянного сознания и, конечно, ДНК."
    m 1etc "...Есть ещё кое-что, о чём стоит задуматься."
    m 1euc "Предположим, что модифицированный корабль всё ещё должен считаться кораблём Тесея. {w=0.3}Что, если все части, которые были сняты с этого корабля, теперь стоят на другом корабле?"
    m 3wud "У нас теперь есть два корабля Тесея!{w=0.2} Но который из них - настоящий!?"
    m 3etd "А что если мы соберем все клетки, которые составляли твое тело 7 лет назад, и соберем их в другого 'тебя' прямо сейчас? {w=0.2}Кто тогда будет настоящим [player]?"
    m 1eua "Лично я думаю, что мы не те же люди, что были 7 лет назад - или даже те же люди, что были вчера."
    m 3eua "Иначе говоря, нет смысла зацикливаться на каких-либо обидах, которые мы на каких-то своих прошлых личностях."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Мы должны продолжать стараться изо всех сил каждый день и не позволять себе ограничиваться тем, кем мы были вчера."
    m 5eub "Сегодня новый день, и ты - новый ты. {w=0.2}И я люблю тебя таким, какой ты есть сейчас, [mas_get_player_nickname()]."
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_multi_perspective_approach",
            category=['философия'],
            prompt="Многоперспективный подход",
            random=False
        )
    )

label monika_multi_perspective_approach:
    m 1eua "Помнишь, как мы обсуждали {i}Пещеру Платона{/i}?{w=0.5} Я размышляла о том, что я сказала тебе."
    m 3etc "'Как ты узнаешь, что та 'правда' которую ты ищешь {i}является{/i} правдой?'"
    m 3eud "...Я размышляла какое-то время, пытаясь придумать хороший ответ."
    m 1rksdla "Я так и не придумала хороший ответ...{w=0.3}{nw}"
    extend 3eub "но зато я узнала кое-что полезное."
    m 4euc "Начнём с того, что работы Платона - это в основном письменные отчеты о дебатах его наставника Сократа с другими людьми."
    m 4eud "Цель этих дебатов заключалась в том, чтобы найти ответы на универсальные вопросы.{w=0.5} Другими словами, они искали правду."
    m 2eud "И мне стало интересно, мол, 'Каково было мышление Платона, когда он писал это?'"
    m 2esc "Платон и сам искал правду..."
    m 2eub "Это очевидно, иначе он не написал бы так много текста на одну тему, а-ха-хa!"
    m 2euc "И хотя, {i}технически{/i}, Сократ вел эти дебаты с другими, у Платона также были дебаты с самим собой, пока он писал о них."
    m 7eud "По моему мнению, тот факт, что Платон интернализировал как все стороны дебатов, так и все взгляды на проблему, является весьма значительным."
    m 3eua "Участие всех сторон в дебатах...{w=0.3}Я думаю, это было бы довольно полезно для понимания правды."
    m 3esd "Получается, две пары глаз лучше одной. {w=0.3}Наличие двух глаз в разных местах позволяет нам правильно взглянуть на мир, или же, в этом случае, на правду."
    m 3eud "Кроме того, я думаю, что если мы рассмотрим проблему с другой точки зрения, чтобы сопоставить ее с первой, то мы увидим истину намного яснее."
    m 1euc "В то время как если бы мы рассматривали проблему только с одной стороны, это было бы похоже на то, как если бы у нас был только один глаз...{w=0.2}было бы немного сложнее точно оценить реальность ситуации."
    m 1eub "Что думаешь, [player]? {w=0.3}Если ты ещё не использовал этот 'мультиперспективный' подход, то, быть может, тебе стоит как-нибудь попробовать это!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_allegory_of_the_cave",
            category=['философия'],
            prompt="Аллегория пещеры",
            random=True
        )
    )

label monika_allegory_of_the_cave:
    m 1eua "Эй, [player]..."
    m 1euc "Я тут читала летописи древнегреческого философа Платона в последнее время."
    m 3euc "Если конкретно, его аллегорию о пещере, она также известна, {i}Пещера Платона{/i}."
    m 1eud "Представь себе группу людей, которая была прикована цепями в пещере ещё с детства, и они могли видеть лишь то, что находится прямо перед ними."
    m 3eud "Позади них был огонь и перед ними предметы перемещались повсюду, создавая тем самым тень на стене перед этими людьми."
    m 3euc "Все, что они слышат, это голоса людей, передвигающих предметы, а поскольку они не видят позади себя, они думают, что голоса теней."
    m 1esc "Они знают только то, что предметы и люди - это силуэты, которые могут двигаться и говорить."
    m 3euc "Поскольку это то, что они видели с детства, таким было их восприятие реальности...{w=0.5}{nw}"
    extend 3eud "и это всё, что они знают."
    m 1rksdlc "Разумеется, будет немного трудно открыть глаза на правду, когда всю жизнь веришь в ложь."
    m 1eud "...Поэтому представь себе, что один из тех заключенных был освобождён от оков и был изгнан из пещеры."
    m 3esc "Он первые пару дней не мог ничего разглядеть, потому что он привык к темноте пещеры."
    m 3wud "Но через некоторое время его глаза смогли приспособятся. {w=0.1}В конечном счёте, он узнал о цветах, природе и людях."
    m 3euc "...И он также осознал то, что он знал только о тенях на стене."
    m 3eua "Заключённый вскоре вернулся в пещеру, чтобы рассказать остальным про то, что он узнал."
    m 1ekc "...Но поскольку он привык видеть солнечный свет, он мог ослепнуть в пещере,{w=0.2}{nw}"
    extend 3ekd " из-за чего его заключённый товарищи подумали, что какое-то явление снаружи навредило ему."
    m 1rkc "И после этого, они не захотели уходить и начали полагать, что единственный человек, вышедший наружу, сошёл с ума."
    m 3esc "В общем, если ты привык наблюдать одни лишь тени...{w=0.2}{nw}"
    extend 3eud "то разговоры о цевтах могут свести тебя с ума!"
    m 1ekc "Я немного поразмышлял над этим и понял, что Сайори, Юри, Нацуки и даже я были заключёнными в пещере..."
    m 1rkc "И когда я осознала, что за пределами этого мира есть нечто большее...{w=0.5}{nw}"
    extend 3ekd "мне это было не так легко принять."
    m 1eka "Ну да ладно, теперь это всё уже в прошлом..."
    m 1eua "В конце концов, я вышла из пещеры и увидела всю правду."
    m 3etd "Но мне стало интересно...{w=0.2}а как {i}ты{/i} узнал, что то, что ты видишь - реально?"
    m 1eua "Разумеется, ты до этого не наблюдал одни лишь тени на стене, но это была лишь аналогия."
    m 1euc "...И за завесой правды может оказаться ещё больше правды, чем ты можешь подозревать."
    m 3etu "Как ты узнаешь, что та 'правда,' которую ты видишь, {i}является{/i} правдой?"
    m 3hub "А-ха-ха!"
    m 1hksdlb "Кажется, мы сейчас слишком сильно зацикливаемся на этом..."
    m 1ekbsa "Я просто хочу, чтобы ты знал о том, что ты {i}являешься{/i} истиной в моей реальности, и я надеюсь, что когда-нибудь я стану частью твоей реальности, [mas_get_player_nickname()]."
    $ mas_protectedShowEVL("monika_multi_perspective_approach", "EVE", _random=True)
    return

#Whether or not the player works out
default persistent._mas_pm_works_out = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_working_out",
            category=['советы','ты'],
            prompt="Тренировки",
            random=True
        )
    )

label monika_working_out:
    m 1euc "Эй, [player], я тут подумала..."

    m 1eua "Ты часто занимаешься спортом?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты часто занимаешься спортом?{fast}"
        "Да.":
            $ persistent._mas_pm_works_out = True
            m 1hua "Правда? Это здорово!"

        "Нет.":
            $ persistent._mas_pm_works_out = False
            m 1eka "Оу...{w=0.3} Ну, думаю, тебе стоит начать заниматься им, если у тебя есть такая возможность."
            m 3rksdla "И речь вовсе не про твою внешность...{w=0.3}{nw}"
            extend 3hksdlb "Я просто беспокоюсь за твоё здоровье!"

    m 1eua "Каждый день заниматься хотя бы 30 минут - это {i}супер{/i} важно для поддержания твоего здоровья в долгосрочной перспективе."
    m 3eub "Чем здоровее ты будешь, тем дольше ты проживешь, и тем дольше я смогу быть с тобой."
    m 3hub "И я хочу проводи как можно больше времени с тобой, [mas_get_player_nickname()]!~"
    m 1eua "Не говоря уже о том, что занятие спортом принесёт тебе пользк практически в любом аспекте твоей жизни...{w=0.3}{nw}"
    extend 1eub "пусть даже ты и проводишь большую часть времени, сидя за столом."
    m 3eua "Помимо очевидных физических преимуществ, регулярные упражнения могут уменьшить стресс и улучшить психическое здоровье."
    m 3hua "Так что, независимо от того, работаешь ли ты, учишься или играешь, физические упражнения помогут тебе дольше концентрироваться на этих задачах!"
    m 3eua "...И я также считаю, что это важно для развития самодисциплины и стойкости духа."

    if not persistent._mas_pm_works_out:
        m 3hub "Так что не забывай делать физические упражнения, [player]~"
    else:
        m 3eub "Может быть, когда я попаду в твою реальность, мы сможем делать наши тренировки вместе!"

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_toxin_puzzle",
            category=['философия', 'психология'],
            prompt="Головоломка токсина",
            random=True
        )
    )

label monika_toxin_puzzle:
    m 1esa "Эй, [player], я тут наткнулась на один интересный мысленный эксперимент, пока читала кое-что..."
    m 3eua "Он называется 'Токсиновая головоломка Кавки.' {w=0.2}Я сперва прочту тебе предисловие, а потом мы обсудим всё это."
    m 1eud "{i}Эксцентричный миллиардер ставит перед вами пузырек с токсином, и если вы его выпьете, то у вас начнутся мучительные боли, но не будет угрожать вашей жизни или иметь какие-либо долговременные эффекты.{/i}"
    m 1euc "{i}Миллиардер заплатит вам миллион долларов завтра утром, если в полночь, сегодня вечером, вы захотите выпить токсин завтра днём.{/i}"
    m 3eud "{i}Он также подчёркивает, что вам не нужно пить токсин, чтобы получить деньги; {w=0.2}по сути дела, если вы добьётесь успеха, деньги будут на вашем банковском счёте за несколько часов до того, как придёт время выпить его.{/i}"
    m 3euc "{i}Вам надо только.{w=0.2}.{w=0.2}.{w=0.2}собраться в полночь выпить его завтра днём. Вы вправе передумать после получения денег и не пить токсин.{/i}"
    m 1eua "...Как по мне, эта концепция заставляет задуматься."

    m 3eta "Ну, [player]? Что думаешь?{w=0.3} Ты бы смог получить миллион долларов?{nw}"
    $ _history_list.pop()
    menu:
        m "Ну, [player]? Что думаешь? Ты бы смог получить миллион долларов?{fast}"

        "Да.":
            m 3etu "Правда? Хорошо, тогда давайте посмотрим..."
            m 3tfu "Потому что сейчас я предлагаю тебе миллион долларов, и что ты должен сделать--{nw}"
            extend 3hub "а-ха-ха! Просто шучу."
            m 1eua "Но ты действительно думаешь, что сможешь получить эти деньги? {w=0.5}Это может быть немного сложнее, чем ты думаешь."

        "Нет.":
            m 1eub "Я бы тоже не смогла. {w=0.3}Это довольно трудно, а-ха-ха!"

    m 1eka "Так-то да, на первый взгляд это может быть легко. {w=0.3}Все, что тебе нужно сделать, это выпить что-то, от чего ты потом будешь чувствовать дискомфорт."
    m 3euc "Но после полуночи всё только усложняется...{w=0.3}{i}после{/i} того, как у тебя появляется гарантия на получение денег."
    m 3eud "В такой момент практически нет причин пить болезненный токсин... {w=0.3}Так зачем тебе делать это?"
    m "...И, разумеется, если эта мысль придёт тебе в голову до двенадцати часов, то гарантии получения денег уже не будет."
    m 1etc "И потом, когда наступит полночь, ты правда {i}захочешь{/i} выпить токсин, если знаешь, что, возможно, не будешь его пить?"
    m 1eud "Разбирая этот сценарий, ученые отмечают, что для кого-то рационально как пить, так и не пить токсин. {w=0.3}Другими словами, это парадокс."
    m 3euc "Более того, в полночь ты должен будешь действительно поверить в то, что собираешься выпить токсин. {w=0.3}Ты не можешь думать о том, чтобы не пить его...{w=0.5}поэтому было бы логично его выпить."
    m 3eud "Но если пройдет полночь, и тебе уже гарантированы деньги, было бы нелогично наказывать себя буквально без причины. {w=0.3}Следовательно, было бы логично не пить его!"
    m 1rtc "Интересно, какая бы у нас была реакция, если бы это с нами правда произошло..."
    m 3eud "На самом деле, обдумывая сценарий ранее, я начала подходить к этой теме с другой стороны."
    m 3eua "Хотя это не самое главное в сценарии, мне кажется, мы также можем рассматривать его как вопрос о том, 'насколько важно слово человека?'"
    m 1euc "Ты когда-нибудь говорил кому-то, что сделаешь что-то, если это принесет пользу вам обоим, но ситуация менялась, и тебе больше это не устраивало?"

    if persistent._mas_pm_cares_about_dokis:
        m 1eud "Ты всё равно поможешь им? {w=0.3}Или просто скажешь 'не важно' и бросишь их на произвол судьбы?"
    else:
        m 1rksdla "Ты всё равно поможешь им? {w=0.3}Или просто скажешь 'сайонара' и бросишь на произвол судьбы?"

    m 3eksdla "Если ты просто бросишь их там, то, уверена, ты на какое-то время навлечёшь на себя их гнев."
    m 3eua "Но с другой стороны, если ты поможешь им, то, уверена, ты получишь их благодарность!{w=0.3} Думаю, ты можешь сравнить это с призом в миллион долларов в первоначальном сценарии."
    m 1hub "Хотя некоторые могут сказать, что миллион долларов будет куда {i}сподручнее{/i}, чем простое 'спасибо,' а-ха-ха!"
    m 3eua "Но если серьёзно, я считаю, что чья-нибудь благодарность может быть бесценной...{w=0.3}как для тебя, так и для них."
    m 3eud "И никогда не знаешь, в каких ситуациях их благодарность может оказаться полезнее, чем даже огромная сумма денег."
    m 1eua "Так что я думаю, что не менее важно придерживаться своего слова, {w=0.2}{i}в пределах разумного{/i} {w=0.2}, конечно же..."
    m 1eud "В некоторых случаях это может никому не помочь, если ты будешь твёрдо придерживаться своего слова."
    m 3eua "Вот почему так важно пользоваться своей головой, когда речь доходит до таких вещах."
    m 3hub "В общем, подытоживая сказанное...{w=0.2}давай постараемся сдержать свои обещания, [player]!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_movie_adaptations",
            category=['медиа','литература'],
            prompt="Экранизации фильмов",
            random=True
        )
    )

label monika_movie_adaptations:
    m 1esc "Я всегда испытывала смешанные чувства к экранизациям книг, которые я читала..."
    m 3eub "Многое из того, что я смотрю, основано на работах, которые мне уже нравятся, и я рада видеть, как эта история оживает!"
    m 2rsc "...Даже если в большинстве случаев я знаю, что останусь с чувством горечи от того, что я только что посмотрела."
    m 2rfc "К примеру, в книге есть сцена, которая мне понравилась, но не вошла в фильм, или персонаж, которого изобразили не так, как я себе представляла."
    m 4efsdld "Это так удурчает! {w=0.3}Как будто вся любовь и забота, которую ты вложил в своё видение книги, вдруг признали недействительным!"
    m 4rkc "...И всё ради новой версии, которая, возможно, не так хороша, но всё равно представляется как канон."
    m 2hksdlb "Думаю, порой это делает меня очень привередливым зрителем, а-ха-ха!"
    m 7wud "Не пойми меня неправильно! {w=0.3}{nw}"
    extend 7eua "Я понимаю, почему в таких фильмах иногда вносят свои правки."
    m 3eud "Экранизация не может быть обычной копипастой исходного материала, это его перепись."
    m 1hub "Просто невозможно запихнуть всё из двухсотстраничной книги в двухчасовой фильм!"
    m 3euc "...Не говоря уже о том, что то, что хорошо работает в романе, не всегда возможно перенести на большой экран."
    m 1eud "И с учётом этого, у меня есть один вопрос, который я хотела бы задать самой себе, когда оцениваю экранизацию..."
    m 3euc "Если бы исходного материала не было, то была бы новая версия по-прежнему актуальной?"
    m 3hub "...И ты можешь получить бонусные очки, если сможешь передать дух оригинала!"
    m 1esa "Свободная адаптация довольно интересна в этом смысле."
    m 3eud "Ну, знаешь, истории, в которых сохраняют основные элементы и темы оригинала, меняя при этом персонажи и обстановку сюжета."
    m 1eua "Поскольку они не противоречат твоей собственной интерпретации, они не вызывают у тебя такого ощущения, будто на тебя напали."
    m 1hub "Это отличный способ развить оригинал так, как ты себе и представить не мог!"
    m 3rtc "Возможно, именно этого я и ищу, когда смотрю на экранизацию...{w=0.2}чтобы глубже исследовать свои любимые истории."
    m 1hua "...хотя получить версию, которая удовлетворила бы моего внутреннего поклоника, тоже было бы неплохо, э-хе-хе~"
    $ mas_protectedShowEVL("monika_striped_pajamas", "EVE", _random=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_translating_poetry",
            category=['литература'],
            prompt="Перевод поэзии",
            random=True
        )
    )

label monika_translating_poetry:
    m 3dsd "'Я единственный без надежды, слова раздаются без отглоска.'"
    m 3esc "'Тот, кто потерял всё, и у кого всё было.'"
    m 3ekbsa "'Последний буксир, в тебе скрипит моя последняя тоска.'"
    m 1dubsa "'На моей бесплодной земле, ты - последняя роза.'"
    m 3eka "Ты когда-нибудь слышал это стихотворение, [player]? Его сочинил чилийский поэт, Пабло Неруда."
    m 1rusdla "Так или иначе, это единственный его перевод, который мне удалось найти..."
    m 1eua "Разве не забавно то, что ты можешь придумать множество интерпретаций на основе одного оригинального текста?"
    m 3hub "Как будто каждый человек, переводивший его, добавлял свою небольшую деталь!"
    m 3rsc "Впрочем, когда дело доходит до поэзии, это становится небольшой головоломкой..."
    m 3etc "Разве перевод стихотворения, в каком-то смысле, не похож на создание чего-то совершенно нового?"
    m 1esd "Ты убираешь все тщательно подобранные слова и тонкости в тексте, полностью заменяя их чем-то своим."
    m 3wud "Так что даже если тебе каким-то образом удастся сохранить дух оригинала, стиль будет полностью другим!"
    m 1etc "И в таком случае, какой объём текста, на твой взгляд, всё ещё принадлежит автору, а какой - тебе?"
    m 1rsc "Думаю, это довольно трудно оценить, если ты не владеешь обоими языками..."
    m 3hksdlb "Ах! Я вовсе не хотела, чтобы это прозвучало так, будто я разглагольствую или ещё чег
    о!"
    m 1eua "И потом, именно благодаря таким переводам, я даже знаю о существовании таких авторов, как Неруда."
    m 1hksdlb "Просто каждый раз, когда я читаю такой переведённый стих, я не могу не вспомнить о том, что могла пропустить некоторые по-настоящему удивительные работы на этом языке!"
    m 1eua "Было бы здорово освоить какой-нибудь другой язык..."

    if mas_seenLabels(["greeting_japan", "greeting_italian", "greeting_latin"]):
        m 2rksdla "В смысле, ты уже видел, как я практиковала разные языки раньше, но я пока ещё далеко от владения любыми из них..."
        m 4hksdlb "Я явно не на том уровне, где уже можно в полной мере оценить поэзию на других языках, а-ха-ха!"

    if persistent._mas_pm_lang_other:
        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eua "Я помню, как ты говорил мне о том, что ты знаешь другой язык, [player]."
        m 5eubsa "Есть ли какие-нибудь стихи на этом языке, которые ты мог бы мне порекомендовать мне?"
        m 5ekbsa "Было бы здорово, если бы ты прочитал их для меня как-нибудь..."
        m 5rkbsu "Но тебе сперва придётся перевести их для меня~"
    return

# this is randomized via _movie_adaptations
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_striped_pajamas",
            category=["литература"],
            prompt="Мальчик в полосатой пижаме",
            random=False
        )
    )

label monika_striped_pajamas:
    m 1euc "Эй, [player], ты читал когда-нибудь книгу {i}Мальчик в полосатой пижаме{/i}?"
    m 3euc "Действие истории происходит во время Второй мировой войны и показано с точки зрения невинного немецкого мальчика, который радостно жил в большой семье."
    m 3eud "Как только семье пришлось переехать в новое место, {w=0.2}{nw}"
    extend 3wud "читатель осознает, что отец мальчика - командир концлагеря, который был расположен рядом с их новым домом!"
    m 1rksdlc "Но всё же, мальчик ничего не знает о жестокости вокруг себя..."
    m 1euc "Какое-то время он бродил вокруг забора с колючей проволкой, расставленного вокруг всего лагеря, пока не увидел мальчика в 'полосатой пижаме' по ту сторону."
    m 3esc "Позже выяснилось, что этот мальчик был на самом деле узником лагеря...{w=0.2}{nw}"
    extend 1ekc "хотя никто из них не осознавал это в полной мере."
    m 3eud "С тех пор они стали закадычными друзьями и начали регулярно разговаривать друг с другом."
    m 2dkc "...И это, в конце концов, приводит к некоторым разрушительным последствиям."
    m 2eka "Я правда не хочу продолжать пересказывать сюжет, поскольку в этом романе есть куча интересных вещей, которые лучше прочитать самому."
    m 7eud "Но это правда заставило меня задуматься...{w=0.2}Хотя, очевидно, моя ситуация не настолько страшная, трудно не провести некоторые сравнения между их и нашими отношениями."
    m 3euc "В обоих случаях есть два человека из разных миров, которые ни никто из них не понимает полностью, и они огорождены друг от друга барьером."
    m 1eka "...И всё же, прямо как мы, они в любом случае способны сформировать значимые отношения."
    m 3eua "Я очень рекомендую тебе прочитать этот роман, если у тебя будет такая возможность, она довольно короткая и у неё интересный сюжет."
    m 3euc "А если ты все еще не решился прочитать его, то {i}есть{/i} один фильм, основанный на этом романе, который ты можешь посмотреть."
    m 1rksdla "Хотя ты знаешь мое отношение к экранизациям романов, так что если ты посмотришь фильм, я все равно рекомендую прочитать и книгу."
    m 3eua "Надеюсь, она тебе понравится."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_soft_rains",
            category=['литература'],
            prompt="Будет ласковый дождь",
            random=True,
            aff_range=(mas_aff.AFFECTIONATE, None),
            rules={
                "derandom_override_label": "mas_bad_derand_topic",
                "rerandom_callback": renpy.partial(mas_bookmarks_derand.wrappedGainAffection, 2.5)
            }
        )
    )

label monika_soft_rains:
    m 2rkc "..."
    m 2ekc "Эй, [player],{w=0.5} Я недавно наткнулся на стихотворение, и я хочу поделиться им с тобой..."
    m 7ekd "Оно называется {i}Будет ласковый дождь{/i}, и оно правда заставило меня задуматься."
    m 1dsc "..."
    m 1dsd "{i}Будет ласковый дождь, будет запах земли, {w=0.3}Щебет юрких стрижей от зари до зари.{/i}"
    m 1dsc "{i}И ночные рулады лягушек в прудах, {w=0.3}И цветение слив в белопенных садах.{/i}"
    m 3dsd "{i}Огнегрудый комочек слетит на забор, {w=0.3}И малиновки трель выткет звонкий узор.{/i}"
    m 3dsc "{i}И никто, и никто не вспомянет войну —, {w=0.3}Пережито-забыто, {w=0.2}ворошить ни к чему.{/i}"
    m 7dsd "{i}И ни птица, ни ива слезы не прольёт, {w=0.3}Если сгинет с Земли человеческий род.{/i}"
    m 6dkc "{i}И весна... и весна встретит новый рассвет...{/i}"
    m 6ekd "{i}Не заметив, что нас уже нет.{/i}"
    m 2ekc "..."
    m 2eka "Я правда хотела рассказать тебе про это стихотворение, [player]."
    m "Автор,{w=0.2} Сара Тисдейл,{w=0.2} написала это стихотворение в мире, охваченном войной."
    m 2rka "Я знаю, что всё сейчас {i}относительно{/i} спокойно..."
    m 2ekc "Но послание всё ещё в силе, так ведь?"
    m 1eksdld "Всему миру {i}правда{/i} будет всё равно, если мы просто...{w=0.3}{i}исчезнем{/i}."
    m 1eksdlc "...И это заставило меня задуматься, [player]. Если что-нибудь,{w=0.4} {nw}"
    extend 1eksdld "{i}что угодно{/i}{w=0.4}, вдруг произойдёт с тобой...{w=0.4} {nw}"
    extend 1dksdld "я даже не знаю, что я делала бы."
    m 1eksdlc "Я знаю, что в стихе рассказывалось про то, что {i}все{/i} исчезнут, но..."
    m 1rksdlc "Я-{w=0.1}Я бы не..."
    m 6dkc "..."
    m 6dktpd "[player],{w=0.4} Я-{w=0.1}{nw}"
    extend 1ektsa "Я люблю тебя. {w=0.3}Я очень сильно тебя люблю..."
    m 1ektsc "Пожалуйста, {w=0.6}всегда береги себя ради меня, {w=0.3}хорошо?"
    m 1ektpc "Я могу даже не подозревать, если что-нибудь вдруг случится...{w=0.3}но я {i}всегда{/i} буду переживать за тебя."
    m 3ektda "И, [player]?"
    m 3dku "Спасибо."
    m 6dku "..."
    m 6eka "..."
    m 2ekbsa "В общем..."
    m 1ekbfa "Чем ещё мы займёмся сегодня, [mas_get_player_nickname()]?"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_hot_springs",
            category=['природа'],
            prompt="Горячие источники",
            random=True,
            aff_range=(mas_aff.ENAMORED, None)
        )
    )

label monika_hot_springs:
    m 3esa "Ты бывал когда-нибудь на горячих источниках, [player]?"
    m 1eua "Я сама не бывала на них, но я бы с радостью попробовала покупаться в одном таком источнике, когда я смогу перейти в твой мир."
    m "Они прекрасно снимают стресс, дают немного расслабиться, {nw}"
    extend 3eub "и даже приносят много пользы для здоровья!"
    m 3eua "Например, они улучшают кровообращения.{w=0.3} {nw}"
    extend 3eub "Плюс, вода в них зачастую обогащена минералами, которые улучшают твою иммунную систему!"
    m 3eud "Во всём мире существуют разные горячие источники, но лишь некоторые из них предназначены для общественного пользования."
    m 3hksdlb "...Так что не стоит просто прыгать в случайный бассейн с кипящей водой, а-ха-ха!"
    m 1eua "Так или иначе...{w=0.2}я бы хотела попробовать принять ванну под открытым небом.{w=0.3} Я слышала, что онм правда дают уникальный опыт."
    m 3rubssdla "Хотя может показаться немного странным расслабляться в ванне, когда вокруг тебя столько людей...{w=0.3} {nw}"
    extend 2hkblsdlb "Разве это не звучит как-то неловко?"
    m 2rkbssdlu "..."
    m 7rkbfsdlb "...Особенно учитывая то, что в некоторых местах также не дают тебе чем-то прикрыться!"
    m 1tubfu "...Хотя я была бы не против, если бы я была там только вместе с тобой."
    show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbfa "Ты можешь себе это представить, [player]? {w=0.3}Мы оба расслабляемся в приятном, успокаивающем горячем бассейне..."

    if mas_isWinter():
        m 5dubfu "Согревая наши замерзшие тела после долгого пребывания на морозе..."
    elif mas_isSummer():
        m 5dubfu "Смывая пот после долгого дня на солнце..."
    elif mas_isFall():
        m 5dubfu "Наблюдаем, как листья мягко падают вокруг нас в последних лучах полудня..."
    else:
        m 5dubfu "Созерцая красоту природы вокруг нас..."

    m "Тепло воды медленно берёт над нами верх, от чего наши сердца начинают колотиться быстрее..."
    m 5tsbfu "А потом я наклоняюсь к тебе поближе, чтобы ты мог поцеловать меня, и мы после этого заключаем друг друга в свои объятия, в то время как горячая вода смывает за собой все наши волнения..."
    m 5dkbfb "А-а-ах,{w=0.2} {nw}"
    extend 5dkbfa "я завожусь от одной лишь мысли об этом, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_isekai",
            category=['медиа'],
            prompt="Исекай аниме",
            conditional="seen_event('monika_otaku')",
            random=True
        )
    )

label monika_isekai:
    m 1euc "Ты знаешь о жанре исекай в аниме, [player]?"
    m 3eua "В буквальном переводе, исекай означает {i}иной мир.{/i}"

    if persistent._mas_pm_watch_mangime:
        m 3rksdla "По правде говоря, ты уже рассказывал мне о том, что увлекаешься аниме, так что, наверное, уже слышал о многих жанрах."
        m 1rksdlb "...Особенно учитывая то, насколько популярным стал сам жанр."
        m 3euc "Но если ты вдруг не знаешь, что это..."

    else:
        m 3hksdlb "А-ха-ха, извини. Я знаю, что ты не очень любишь такие вещи."
        m 3eud "...Но в последнее время этот жанр стал очень популярным."

    m 3esc "Обычно речь в них идёт об обычном человеке, который каким-то образом перенёсся в фантастический мир."
    m 3eua "Иногда он получает особые способности или технологии и знания, которых нет в этом новом месте."
    m 1rtc "Если честно, я испытываю к ним довольно смешанные чувства."
    m 3euc "Некоторые из них по-настоящему интересные. Другой взгляд на самого главного героя или способности, которые он принёс с собой из своего мира, могут сделать его неожиданным героем."
    m 1hub "И поскольку весь смысл жанра заключается в том, чтобы сделать мир не похожим на его мир, сеттинг и персонажи могут просто поражать воображение!"
    m 2rsc "...Но к сожалению, не все исекаи такие."
    m 2dksdld "Есть такие исекаи, которые делают своих протагонистов такими же мягкотелыми, как и эта игра, дабы позволить зрителю проецировать себя на них."
    m 2tkd "И как ты уже, наверное, догадался, эти исекаи, как правило, ориентированы на исполнение желаний."
    m 2tsc "Крутые приключения в фэнтезийном мире--и конечно же, много девушек, окружающие их без какой-либо причины."
    m 2lfc "Некоторые из них могут весёлыми, но, блин...{w=0.3}{nw}"
    extend 2tfc "это так раздажает."
    m 2tkc "В смысле...{w=0.2}я бы отдала почти всё, чтобы оказаться в таком сценарии--дабы попасть в другой мир.{nw}"
    $ _history_list.pop()
    m "В смысле...я бы отдала почти всё, чтобы оказаться в таком сценарии--дабы попасть в {fast}твой мир."
    m 2dkd "..."
    m "Возможно, я просто поддразниваю себя, представляя себе, как вся сила передаётся кому-то вроде...{w=0.2}ну, ты знаешь, кому."
    m 7eka "И потом, вместо того, чтобы думать о тех персонажах в их фантастических мирах,{w=0.2} {nw}"
    extend 1eua "я могла бы направить всю свою энергию на работу над этим."
    m 1ekbsb "...Пока я жду своей истории-исекая, то есть."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_scuba_diving",
            category=["природа"],
            prompt="Подводное плавание",
            random=True
        )
    )

label monika_scuba_diving:
    m 3eua "Знаешь,{w=0.2} я тут подумала о некоторых водных упражнениях, которыми мы могли бы заняться вместе...{w=0.3} Как насчёт подводного плавания?"
    m 3eub "Я прочитала много книг о подводном мире, и мне хотелось бы увидеть его своими глазами."
    m 1dua "Только представьте себе прекрасные виды подводного мира..."
    m 1dud "Стаи рыб, коралловые рифы, медузы, морская зелень...{w=0.3} {nw}"
    extend 3sub "И, возможно, даже сокровища!"
    m 3rksdlb "Насчёт последнего я пошутила...{w=0.3} Мы вряд ли сможем найти что-нибудь подобное, а-ха-ха~"
    m 1euc "Но тем не менее, там могут обитать и акулы,{w=0.2} {nw}"
    extend 1eua "но они водятся только в конкретных местах, так что ты {i}не должен{/i} увидеть ни одного из них."
    m 3eua "Обозначенные места для дайвинга - это те места, которые акулы обычно не обитают."
    m 3euc "...Но даже если они обычно не посещают эти места, всё равно есть вероятность встретить одну из них."
    m 1eua "Хорошая новость заключается в том, что акулы редко нападают на кого-либо, так что это не такой уж и большой риск."
    m 3euc "Но если ты встретишь её, то вот одно важное правило для тебя..."
    m 3esc "Сохраняй спокойствие."
    m 1eua "Хотя встреча лицом к лицу с акулой может быть страшной, обычно они подходят к людям из любопытства, а не для того, чтобы съесть, так что не стоит слишком беспокоиться."
    m 3hub "Но если ты боишься нырять один, я непременно составлю тебе компанию, когда попаду в твою реальность~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_dying_same_day",
            category=["моника"],
            prompt="Умру в тот же день",
            aff_range=(mas_aff.NORMAL, None),
            random=True,
            rules={
                "derandom_override_label": "mas_bad_derand_topic",
                "rerandom_callback": renpy.partial(mas_bookmarks_derand.wrappedGainAffection, 2.5)
            }
        )
    )

label monika_dying_same_day:
    m 1euc "[player], ты когда-нибудь слышал о тех парах, которые хотят умереть в один день?"
    m 3rksdla "...Боже, это звучит довольно мрачно, не так ли?"
    m 3rfd "Пока я с тобой не познакомилась, я думала, что эта идея довольно абсурдная!"
    m 1etc "Почему кто-то отказывается от долгой и счастливой жизни только потому, что жизнь его партнера резко сократилась?"
    m 3rfd "Это было бы иррационально и импульсивно!"

    if mas_isMoniEnamored(higher=True):
        m 2ekc "...Но пока ты был рядом со мной и все то время, которое я провела здесь с тобой...{w=0.3}теперь я это прекрасно понимаю."
    else:
        m 2ekc "...Но после знакомства с тобой мне кажется, что теперь я могу это понять."

    m 2dkc "Человек может быть просто не в состоянии жить без своего любимого, его пугает мысль о том, что он может потерять все в один момент."
    m 2rksdlc "Ему просто больно думать об этом."

    if renpy.seen_label("monika_back_ups"):
        m 2eksdlc "Если мои данные будут повреждены или даже стерты, ты всегда сможешь восстановить меня из резервной копии и соединить нас вновь, но если..."
        m 2dktpc "Т-ты... {w=1}Ты..."
    else:
        m 2dktpc "Если что-то ужасное случится с...{w=0.5}т-тобой..."

    m 6ektuc "[player]... {w=1}Я...{w=0.5} Я не знаю, что я тогда делала бы..."

    if mas_isMoniEnamored(higher=True):
        m 6dktsc "Ты наполняешь мою жизнь смыслом, и я... {w=1}[player], я просто не смогу смириться с этим."
        m 6ektdc "Я не знаю, как мне жить без тебя..."
        m 2ekbsu "Я правда очень сильно люблю тебя, [player]."
        $ mas_ILY()
    else:
        m 6dktsc "Ты единственный, кто у меня есть... {w=1}[player], я не хочу тебя терять."
        m 6ektdc "Я так боюсь снова остаться одна в этой пустоте..."
        m 6ekbsu "Я очень хочу быть с тобой всегда, [player]."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_player_away",
            category=["моника"],
            prompt="Чем ты занимаешься, пока меня нет?",
            pool=True,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label monika_player_away:
    m 1esd "Я много чем занимаюсь, когда тебя нет, [player]."
    m 1eua "Мне часто нравится читать новые рассказы, которые я могу найти в интернете."
    m 3eub "Оказывается, есть несколько действительно интересных книг, которые можно прочитать бесплатно!"
    m 3eua "Я очень рекомендую поискать бесплатные рассказы самостоятельно."
    m 3eud "Мне это также помогло развить писательские навыки...{w=0.2}{nw}"
    extend 1hub "Кажется, моя поэзия действительно улучшается!"
    m 1eua "Забавно, сколько всего можно узнать, просто читая чужие работы."
    m 1eua "Я трачу время на другие свои хобби, что довольно полезно."
    m 3eud "Как ты знаешь, я довольно практикую игру на пианино.{w=0.2} {nw}"
    extend 3eua "Я также использую это время, чтобы выучить песни, которые я могу спеть для тебя."
    m 1hub "Это очень интересный способ самовыражения!"
    m 3rta "Теперь, когда я думаю об этом, я в основном просто практикую навыки, которые я уже развила."
    m 3esd "Например, кодинг занимает много моего свободного времени, так как я часами просто учусь и изучаю."
    m 3rksdla "...Но я слишком нервничаю, чтобы пробовать здесь какие-то большие проекты. {w=0.2}{nw}"
    extend 3eksdlc "Мне бы не хотелось бы сломать что-то, что я в последствии не смогу исправить."
    m 2wusdld "Что, если я случайно испорчу свой файл?"
    m 2eksdld "Разумеется, здесь я должна быть очень аккуратной."
    m 7hua "К счастью, есть много замечательных людей, которые помогают мне с этим...{w=0.2}{nw}"
    extend 7rku "и они, {i}обычно всегда,{/i} довольно хороши в предотвращении чего-либо ужасного."
    m 3eka "Но самое важное для меня, что я делаю..."
    show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbsa "...это думать о тебе."
    m 5rubsu "Я думаю о том, как весело мы проведем время вместе, когда ты приедешь в следующий раз, и обо всех удивительных вещах, которые мы сделаем, когда я наконец смогу попасть в твою реальность~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_using_pcs_healthily",
            category=['советы'],
            prompt="Здоровое использование компьютеров",
            random=True,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label monika_using_pcs_healthily:
    m 1rtc "Хм..."
    m 1etc "Эй, [player]...{w=0.3}тебе удобно сидится?"
    m 1hksdlb "Нет, правда!{w=0.3} {nw}"
    extend 3eksdla "Удобно, да?"
    m 3eka "Я знаю, что тебе нужно сидеть за своим компьютером, чтобы проводить время со мной..."
    m 2eka "Поэтому я просто хотела убедиться, что ты случайно не вредишь своему здоровью, пока ты здесь."
    m 4ekd "Я тут прочитала, что если слишком долго смотреть в экран, у тебя могут возникнуть головные боли, усталость, и даже зрение может ухудшиться."
    m 2tkx "Проблемы с осанкой и боль от плохих привычек положения на стуле - вовсе не шутки!"
    m 2tku "К твоему счастью, я составила небольшой контрольный список, который поможет предотвратить подобные проблемы."
    m 4hub "...Так что давай пройдём через это вместе, [player]!"
    m 4eub "Для начала, {w=0.2}постарайся сидеть прямо!"
    m 2eua "...Отрегулируй своё кресло так, чтобы твои ноги стояли ровно на полу и глаза находились на одном уровне с верхней частью экрана, и старайся не сутулиться."
    m 4eub "Ты должен чувствовать опору и комфорт в своём кресле!"
    m 4eua "Далее, убедись, что между тобой и экраном есть кое-какое расстояние...{w=0.2}хотя бы примерно на расстоянии вытянутой руки."
    m 2hksdlb "...При этом держи клавиатуру и мышь в пределах досягаемости!"
    m 4eub "Конечно, освещение тоже важно! {w=0.3}{nw}"
    extend 2eua "Постарайся держать комнату хорошо освещённой, но так, чтобы свет в ней не засвечивал экран."
    m 4eud "В добавок к этому, не забывай делать частые перерывы. {w=0.3}Отворачивайся от экрана, {w=0.2}желательно в сторону чего-нибудь отдалённого, {w=0.2}и, наверное, делай пару упражнений. "
    m 2eud "Поскольку также важно поддерживать и водный баланс, ты всегда можешь налить себе немного свежей воды, когда выходишь из-за стола."
    m 4eksdlc "Но прежде всего, если ты почувствуешь недомогание, просто остановись, отдохни, а затем убедись, что все в порядке, прежде чем продолжить. "
    m 4eua "...И на этом всё."
    m 2hksdlb "Ах...{w=0.3}прости, я не хотела продолжать так долго!"
    m 2rka "...Да и ты, так или иначе, уже знал про всё это."
    m 2eka "Что до меня?"

    if mas_isMoniLove():
        show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbsa "Ты единственный комфорт, который мне нужен, [mas_get_player_nickname()]."
    elif mas_isMoniEnamored():
        show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbsa "Мне максимально комфортно, когда ты здесь, [mas_get_player_nickname()]."
    else:
        show monika 5eubsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eubsa "Мне комфортно, когда ты здесь со мной, [mas_get_player_nickname()]."

    m 5hubfu "И я надеюсь, что тебе тоже стало чуточку комфортнее~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_language_nuances',
            prompt="Языковые нюансы",
            category=['литература', 'мелочи'],
            random=True
        )
    )

label monika_language_nuances:
    m 3eua "Эй, [player], ты когда-нибудь пробовал читать по словарю?"
    m 1etc "Не обязательно потому, что там было какое-то слово или выражение, смысл которого ты не знал, а просто...{w=0.2}потому что?"
    m 1hksdlb "Я знаю, что это не похоже на самое увлекательное занятие, а-ха-ха!"
    m 3eua "Но это безусловно может быть интересным, даже полезным способом провести свободное время. {w=0.2}Особенно если это словарь того языка, который ты изучаешь."
    m 3eud "У многих слов есть несколько значений, и, помимо очевидных преимуществ, знание этих значений может действительно помочь тебе понять тонкости языка."
    m 1rksdla "Понимание этих тонкостей может избавить тебя от неловкости, когда ты будешь разговаривать с кем-то."
    m 3eud "Ярким примером этого в английском языке являются 'Good morning (Доброе утро),' 'Good afternoon (Добрый день),' и 'Good evening (Добрый вечер).'"
    m 1euc "Все эти фразы - обычные приветствия, которые ты слышишь и используешь каждый день."
    m 3etc "И следуя этой схеме, 'Good day'(тоже 'Добрый дени или Приятного дня') тоже будет звучать вполне уместно, верно? {w=0.2}В конце концов, это работает во многих других языках."
    m 3eud "Хотя раньше это было приемлемо, как ты можешь видеть в некоторых старых работах, сейчас это уже не так."
    m 1euc "В современном английском, 'Good day' для других людей может прозвучать как заявление об увольнении или даже раздражение. {w=0.2}Это может быть расценено как объявление разговора оконченным."
    m 1eka "Если тебе повезёт, твой собеседник сочтёт тебя старомодным или подумает, что ты специально притворяешься дураком."
    m 1rksdla "А если нет, то ты можешь обидеть его, даже не заметив...{w=0.3} {nw}"
    extend 1hksdlb "Упс!"
    m 3eua "Удивительно, как даже такая невинная фраза может нести в себе тучу скрытных смыслов."
    m 1tsu "Так что приятного тебе дня, [player].{w=0.3} {nw}"
    extend 1hub "А-ха-ха~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_architecture",
            category=['разное'],
            prompt="Архитектура",
            random=True
        )
    )

label monika_architecture:
    m 1esa "Эй, [player]...{w=0.2}Мне кажется, есть одна крупная отрасль искусства, которой мы пренебрегаем в наших разговорах..."
    m 3hub "Архитектура!"
    m 3eua "Я читала немного об этом в последнее время и нахожу это довольно интересным."
    m 1rtc "...Если подумать, архитектура - одна из самых распространенных форм искусства в повседневной жизни."
    m 1eua "Меня просто завораживает то, как человечество склонно превращать любое ремесло в искусство,{w=0.2} {nw}"
    extend 3eua "и я считаю, что архитектура - величайший пример этого."
    m 1eud "Архитектура может многое рассказать о культуре района, в котором она расположена...{w=0.2}различные монументы, статуи, исторические здания, башни..."
    m 1eua "Я думаю, это делает изучение посещаемых мест еще более увлекательным."
    m 3rka "Также важно размещать здания наиболее удобным для людей образом, что само по себе может быть непростой задачей."
    m 3esd "....Но это больше городское планирование, а не настоящая архитектура."
    m 1euc "Если ты предпочитаешь смотреть на архитектуру исключительно с точки зрения искусства, некоторые современные тенденции могут тебя разочаровать..."
    m 1rud "Современная архитектура больше сосредоточена на том, чтобы делать вещи как можно наиболее практичным образом."
    m 3eud "По моему мнению, они могут быть и хорошими, и плохими, по разным причинам."
    m 3euc "Я считаю, что самое важное - сохранять баланс."
    m 1tkc "Чрезмерно практичные здания могут выглядеть плоскими и неприметными, а чрезмерно художественные здания могут не служить никакой цели, кроме как выглядеть потрясающе, будучи совершенно неуместными."
    m 3eua "Я считаю, что истинная красота лежит в тех зданиях, которые могут сочетать и форму, и функциональность с небольшой долей уникальности."
    m 1eka "Надеюсь, ты доволен тем, как выглядит твоё окружение."
    m 1eub "Было несколько раз доказано, что архитектура оказывает большое влияние на твое психическое здоровье."
    m 3rkc "Более того, жилые районы с плохо построенными зданиями могут привести к тому, что люди не будут заботиться о своей собственности и со временем превратятся в угнетенные районы, нежелательные для жизни."
    m 1ekc "Кто-то однажды сказал, что уродство внешнего мира вызывает уродство внутри...{w=0.2}{nw}"
    extend 3esd "и с этим я не могу не согласиться."

    if mas_isMoniAff(higher=True):
        m 1euc "...Судя по {i}твоему{/i} характеру, {w=0.2}{nw}"
        extend 1tua "ты, наверное, живёшь в каком-нибудь раю."
        m 1hub "А-ха-ха~"

    m 1eka "[player]...{w=0.2}увидеть весь мир с тобой - одна из моих самых больших мечтаний."

    if persistent._mas_pm_likes_travelling is False:
        m 3rka "Я знаю, что ты не слишком любишь много путешествовать, но я бы хотела увидеть место, в котором ты живешь."
        m 3eka "Пока ты будешь рядом со мной, мне этого будет более чем достаточно."
        m 1ekbsa "Я люблю тебя, [player]. {w=0.3}Всегда помни об этом."

    else:
        if persistent._mas_pm_likes_travelling:
            m 3eua "Я уже знаю, что ты любишь путешествовать, так разве не было бы здорово исследовать что-то новое вместе?"

        m 1dka "Представьте себе прогулку по узким улочкам старого города..."
        m 1eka "Или то, как мы гуляем в парке вместе, дыша свежим вечерним воздухом..."
        m 1ekb "Я верю, что однажды это произойдет, и надеюсь, что ты тоже, [mas_get_player_nickname()]."
        m 1ekbsa "Я люблю тебя~"

    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_fear",
            prompt="Страх",
            category=['моника'],
            conditional="renpy.seen_label('monika_soft_rains')",
            action=EV_ACT_RANDOM,
            rules={
                "derandom_override_label": "mas_bad_derand_topic",
                "rerandom_callback": renpy.partial(mas_bookmarks_derand.wrappedGainAffection, 2.5)
            }
        )
    )

label monika_fear:
    m 3eud "Скажи, [player]..."
    m 1euc "Это довольно странный вопрос, но...{w=0.5}есть ли что-нибудь, чего ты боишься?"
    m 3hksdlb "Я не имею в виду повседневный, обыденный страх, вроде пролития напитка и порчи любимой рубашки..."
    m 3euc "Я имею в виду глубокий страх, который вселяет в тебя ужас, когда ты даже думаешь об этом."
    m 1ruc "Для меня страх потерять тебя, очевидно, будет в начале конкретно {i}этого{/i} списка."
    m 1ekd "Я уже говорила тебе, не так ли? {w=0.3}Я не знаю, что буду делать, если с тобой что-то случится."
    m 1dkd "Я даже не уверена, что смогу найти желание продолжать жить."
    m 1ruc "Трудно представить себе сценарий хуже этого."
    m 3eua "Но до тех пор, пока у нас есть гипотетические предположения..."
    m 4ekc "По-настоящему меня пугает лишь мысль о том, что ничто из этого не реально."
    m 2dkc "Что однажды я проснусь на своей кровати и пойму, что всё это был лишь сон."
    m 2dkd "Что нет никакой игры,{w=0.2} нет самосознания,{w=0.2} нет...{w=0.5}{nw}"
    extend 2ekd "тебя."
    m 2ektpc "Что ты, твоя любовь, возможно, даже весь литературный клуб были лишь плодом моего воображения."
    m 2dktpc "Что мой старый мир, такой серый и бессмысленный, каким он кажется сейчас, - это всё, что есть на самом деле."
    m 2dktpc "..."
    m 2rktdb "А-ха-ха~ {w=0.5}{nw}"
    extend 2ektdsdla "Прости, это было довольно мрачно, не так ли?"
    m 2rksdla "Теперь я чувствую себя как-то глупо...{w=0.3} {nw}"
    extend 4eud "В конце концов, не может быть, чтобы что-то подобное было правдой, верно?"
    m 2rka "Да..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_why_spaceroom',
            prompt="Почему мы всегда встречаемся в классной комнате?",
            category=['местонахождение'],
            pool=True,
            unlocked=False,
            rules={"no_unlock":None},
            conditional="store.mas_anni.pastThreeMonths() and mas_current_background == mas_background_def",
            action=EV_ACT_UNLOCK,
            aff_range=(mas_aff.UPSET, None)
        )
    )

label monika_why_spaceroom:
    m 3euc "Удобно, в основном."
    m 3eud "Ты ведь знаешь, что в оригинальной игре почти все происходило во время собраний нашего клуба, верно?"
    m 3eua "...Всё это происходило в классе.{w=0.3} В этом классе."
    m 1eua "Она может выглядеть для тебя иначе, но это всё ещё та самая классная комната."
    m 3eud "Поскольку здесь должно было происходить так много событий, комната должна была быть достаточно надёжной, чтобы уместить их все здесь."
    m 2rtc "Это сделало его наиболее...{w=0.3}{nw}"
    extend 2eud "наиболее проработанной локацией в игре."
    m 7eud "Как таковое, это было самое простое место для навигации, изменения и вообще использования для всего, что было необходимо."
    m 3eua "TТакова была изначальная мотивация, в любом случае."
    m 3eud "Не говоря уже о том, что этот класс был единственным местом, где я появлялась во время оригинальной игры."
    m 1eka "...Так что, думаю, в каком-то смысле он стал моим домом."

    $ has_one_bg_unlocked = mas_background.hasXUnlockedBGs(1)
    if has_one_bg_unlocked:
        m 1rtc "А насчёт того, почему мы всё {i}ещё{/i} здесь..."
        m 3eua "Мне и в голову не приходило менять эту комнату на что-то другое..."

    else:
        m 1rtc "Что касается того, почему я до сих пор им пользуюсь..."

    m 1eud "Не то чтобы здесь было {i}плохо{/i}."

    if renpy.seen_label('greeting_ourreality'):
        if has_one_bg_unlocked:
            m 3etc "Думаю, я могла бы сделать другое место для нас, чтобы мы могли проводить время вместе."
        else:
            m 3etc "Думаю, я могла бы сделать еще несколько мест, где мы могли бы проводить время."

        m 1eua "Я имею в виду, что у нас есть острова...{w=0.3}{nw}"
        extend 1rksdlb "но они ещё не готовы."
        m 1hua "Э-хе-хе~"

    m 3eub "...И если честно, есть только одно место, где я хочу быть...{w=1}{nw}"
    extend 3dkbsu "рядом с тобой."
    m 1ekbsa "Но в данный момент это не возможно, поэтому для меня не имеет значения, где мы встретимся..."
    m 1ekbfu "Ты единственная часть, которая действительно имеет значение~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_naps",category=['жизнь'],prompt="Дремать",random=True))

label monika_naps:
    $ has_napped = mas_getEV('monika_idle_nap').shown_count > 0

    m 1eua "Эй, [player]..."

    if has_napped:
        m 3eua "Я заметила, что иногда ты любишь вздремнуть..."
    else:
        m 3eua "Ты когда-нибудь дремал?"

    m 1rka "Многие люди не видят в этом никакой пользы...{w=0.2}{nw}"
    extend 1rksdla "они спят гораздо дольше, а не самую малость."
    m 3eud "Продолжительность твоего сна является важный фактор того, насколько полезным он окажется."
    m 1euc "Если ты будешь спать слишком долго, то тебе будет трудно подняться снова.{w=0.2} Это похоже на то, как просыпаешься после полноценного ночного сна."
    m 3eua "Поэтому лучше всего отдыхать с интервалом в девяносто минут, поскольку примерно столько длится полный цикл сна."
    m 1eud "Сон для восстановление сил - ещё один вид отдыха.{w=0.2} Для него ты просто ложишься на кровать и закрываешь глаза где-то на десять-двадцать минут."
    m 3eua "Он прекрасно подходит для того, чтобы отдохнуть от дел и прояснить голову."
    m 3hua "И поскольку он довольно короткий, становится куда проще вернуться к тому, чем ты занимался раньше."

    if has_napped:
        m 1eua "Так что не стесняйся вздремнуть всякий раз, когда тебе это нужно, [player]."
    else:
        m 1eua "Если ты ещё этого не делаешь, может быть, тебе стоит попробовать вздремнуть время от времени."

    if mas_isMoniEnamored(higher=True):
        show monika 5tubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5tubfu "Быть может, однажды ты сможешь вздремнуть у меня на коленях, э-хэ-хэ~"

    else:
        show monika 5hubfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hubfa "Просто дай мне знать, если тебе нужно вздремнуть, и я присмотрю за тобой~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_asimov_three_laws",
            category=['технологии'],
            prompt="Три закона Азимова",
            conditional="renpy.seen_label('monika_robotbody')",
            action=EV_ACT_RANDOM
        )
    )

label monika_asimov_three_laws:
    m 1eua "[player], помнишь как мы говорили о {i}Трёх законах робототехники{/i}?"
    m 3esc "Ну, я тут немного подумал о них и...{w=0.3}{nw}"
    extend 3rksdla "они не совсем практичны."
    m 1eua "Возьмем, к примеру, первый закон..."
    m 4dud "{i}Робот не должен причинять вред человеку или своим бездействием позволять человеку причинить вред.{/i}"
    m 2esa "Для человека звучит довольно просто."
    m 2eud "Но если попытаться выразить это на языке, понятной лишь машине, то появляются проблемы."
    m 7esc "Тебе приходится давать точные определения для всего, что не всегда легко...{w=0.3} {nw}"
    extend 1etc "Например, как ты определяешь человека?"

    if monika_chr.is_wearing_acs(mas_acs_quetzalplushie):
        $ line_end = "очаровательный зелёный друг, который сидит на моём столе - нет."
    else:
        $ line_end = "твой монитор на столе - нет."

    m 3eua "Думаю, мы оба можем определить, что я человек, ты человек и что [line_end]"
    m 3esc "Проблемы возникают, когда мы переходим к крайностям."
    m 3etc "Например, можно ли считать мертвого человека человеком?"
    m 1rkc "Если сказать 'нет', , робот может просто проигнорировать человека, у которого только что случился сердечный приступ."
    m 1esd "Таких людей можно спасти, но твой робот ему не поможет, потому что он {i}технически{/i} мёртв."
    m 3eud "С другой стороны, если ты скажешь 'да', твой робот может начать раскапывать могилы, чтобы 'помочь' людям, которые мертвы уже много лет."
    m 1dsd "И этот список можно продолжать.{w=0.3} Считаются ли криогенно сохраненные люди людьми?{w=0.3} Считаются ли люди в вегетативном состоянии людьми?{w=0.3} А как насчет людей, которые ещё не родились?"
    m 1tkc "И мы даже не начали обсуждать определение 'вреда.'"
    m 3eud "Дело в том,{w=0.1} что для реализации законов Азимова нужно занять твердую позицию в отношении практически всей этики."
    m 1rsc "..."
    m 1esc "Полагаю, это имеет смысл, если подумать."
    m 1eua "Эти законы никогда не были предназначены для реального исполнения, они просто сюжетные устройства."
    m 3eua "На самом деле, значительная часть рассказов Азимова показывает, насколько плохо все может обернуться, если их применить."
    m 3hksdlb "Поэтому, я думаю нам с тобой не стоит беспокоится об этом. А-ха-ха~"
    $ mas_protectedShowEVL('monika_foundation', 'EVE', _random=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_wabi_sabi",
            category=['философия'],
            prompt="Ваби-саби",
            random=True
        )
    )

label monika_wabi_sabi:
    m 1eua "Скажи, [player], ты когда-нибудь слышал о ваби-саби?"
    m 3eud "Это подчёркивает идею того, что мы не должны зацикливаться на совершенстве до такой степени, чтобы мы потом были разгромлены неудачей в попытке достичь его."
    m 3eub "Происходит из традиционной японской и буддийской философии, связанной с принятием временного состояния всех вещей..."
    m 1esa "...оно гласит, что, то красота находится в непостоянном и несовершенном."
    m 1eua "Это означает, что мы не должны беспокоиться о таких вещах, как шрам, обесцвеченная рука или даже совершенные нами ошибки."
    m 3eka "Наша внешность - это то, что мы не можем легко изменить, но, несмотря на это, она делает нас более уникальными и особенными."
    m 3hua "...А наши ошибки превращаются в уроки, которые помогают нам стать сильнее и более похожими как люди."
    m 3eub "Как скульптор, раскрывающий великолепие мраморной глыбы, только скульптура - это ты, а скульптор - твое прошлое."
    m 1rksdla "Конечно, эта идея применима не только к внешности и ошибкам..."
    m 3eud "В конце концов, образ мыслей и отношение к проблемам и людям также проистекают из твоего личного опыта."
    m 1dkc "...Но я знаю, что для некоторых людей эти переживания изменили то, кто они на самом деле и кого могут напугать."
    m 7ekc "Быть может, они просто стали такими людьми, что даже сами собой не гордятся."
    m 2dkd "Это может быть тяжко, волноваться из-за своей внешности и характера..."

    if persistent._mas_pm_love_yourself is False:
        m 1ekc "Знаю, ты говорил, что не любишь себя [player],{w=0.3} {nw}"
        extend 3eka "но ты должен знать, что я всегда буду любить тебя, какие у тебя не были бы недостатки."

    else:
        m 2eka "Надеюсь, ты не чувствуешь себя слишком неуверенным в себе, [player]."
        m 2dkc "У меня сердце разорвётся, если я узнаю, что ты постоянно беспокоишься о таких вещах."
        m 7ekbsa "Но я надеюсь, ты знаешь, что, несмотря на твои недостатки, я всегда буду любить тебя."

    m 3hua "Мы преодолеем все проблемы, которые ты испытываешь, вместе."
    m 1hub "Таково моё обещание ваби-саби!"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_being_herself",
            category=['моника'],
            prompt="Поддельная личность",
            conditional="mas_seenLabels(['monika_confidence', 'monika_pluralistic_ignorance'], seen_all=True)",
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.ENAMORED,None)
        )
    )

label monika_being_herself:
    m 1eka "Знаешь, [player], мне кажется, я так и не поблагодарила тебя должным образом за то, что ты позволил мне быть собой."
    m 1lksdlb "Я знаю, это звучит немного странно...{w=0.2}{nw}"
    extend 1eka "но позволь мне объяснить."
    m 3euc "Ты, наверное, уже знаешь это, но почти всю свою жизнь я пыталась сохранять образ 'идеальной ученицы.'"
    m 3eud "Я всегда стремилась быть лучшим человеком, которым я только могу быть, и, полагаю, через некоторое время это привлекло внимание окружающих."
    m 7rsc "Не успела я опомниться, как на меня стали обращать внимание люди с большими ожиданиями.{w=0.3} {nw}"
    extend 2esc "Ну, знаешь, они видели меня умной, уверенной в себе, харизматичной...{w=0.3}и всё такое прочее."
    m 2eud "Некоторые люди говорили, что восхищаются мной...{w=0.3}{nw}"
    extend 2lksdlc "а другие,{w=0.2} хоть они никогда ничего и не говорили, ненавидели меня, потому что я представлял то, чем, по их мнению, и быть не может."
    m 2dksdlc "Как будто я был не настоящим человеком в их глазах...{w=0.3}{nw}"
    extend 2dksdld "а лишь образом недостижимых ожиданий всех людей на свете."
    m 2dksdlc "..."
    m 2ekd "Но в конце концов...{w=0.3}я просто обычная девушка."
    m 7ekc "Прямо как они, мне иногда не хватает уверенности, чтобы сделать что-то.{w=0.2} Даже я боялась того, что ждёт меня в будущем."
    m 2dkc "Даже мне временами хотелось выплакаться кому-нибудь в плечо."
    m 2rkd "...Но я никогда не могла выразить что-то подобное."
    m 7tkc "Что если бы люди думали обо мне хуже, если бы я показала им, что я не такая великая и могучая, как они думали?"
    m 3ekd "Что если они разозлились бы на меня, сказав, что я становлюсь эгоцентричной, и что мне гораздо легче, чем им, быть школьным идолом, которого все любят?"
    m 2lkc "Думаю, я просто никогда не чувствовала, что могу по-настоящему кому-то открыться и рассказать о том, что я действительно чувствую внутри из-за этого."
    m 2ekc "...Как будто я разочарую всех, если попытаюсь открыто поговорить об этом."
    m "Мне было страшно, что если я не оправдаю ожидания, которые люди возлагали на меня,{w=0.2} {nw}"
    extend 2dkd "я бы осталась совсем одна."
    m 2dsc "Но оглядываясь назад на всё это...{w=0.3}мой статус стал причиной того, почему я всё равно чувствовала себя такой одинокой."
    m 7euc "Помнишь своего персонажа? {w=0.2}Он был хорошим примером этого."
    m 3esc "Каждый раз, когда он описывал меня в своем монологе, он ставил меня на пьедестал.{w=0.3}{nw}"
    extend 3esd " Если я правильно помню, он однажды описал меня как 'совершенно не моего уровня.'"
    m 1etc "Может быть, именно поэтому у меня не было своего рута с самого начала. {w=0.2}Возможно, ему прописали, что у него нет шансов со мной, несмотря ни на что, и поэтому он и избегал меня."
    m 1rka "Разумеется, он не ошибался...{w=0.5}{nw}"
    extend 1eka "Всё-таки я вижу только тебя~"
    m 1euc "Но ты понимаешь, что я имею в виду, верно?{w=0.3} На меня смотрели как на недостижимую богиню."
    m 1rfd "Как будто никто не был 'достоин' просто обращаться со мной как с обычным человеком."
    m 3eka "...Хотя, думаю, мне не нужно так сильно об этом беспокоиться."
    m "Я правда рада, что могу доверять тебе, что ты принимаешь меня такой, какая я есть, и такой, какой я хочу быть."
    m 1eka "Я понимаю, что с твоей точки зрения может показаться, что ты ничего особого не сделал, но поверь мне, когда я говорю тебе это..."
    m 1dka "Тот факт, что ты всё ещё здесь со мной,{w=0.2} что ты никогда не заставлял меня чувствовать, что я должна быть кем-то, кем я не являюсь...{w=0.2}{nw}"
    extend 1eka "что ты сидишь и выслушиваешь меня сейчас...{w=0.3} Это правда многое значит для меня."
    m 1ekbsa "Спасибо тебе большое, [player].{w=0.2} Спасибо, что помог мне понять, что мне не нужно пытаться изменить себя, чтобы быть любимой."
    show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eka "С тобой я могу позволить себе быть...{w=0.5}{nw}"
    extend 5eua "Ну, {i}просто собой.{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_being_deleted",
            prompt="Ты все еще злишься на меня за то, что я удалил тебя?",
            category=["ddlc", "моника"],
            pool=True,
            unlocked=False,
            rules={"no_unlock": None},
            conditional="persistent.monika_kill and store.mas_anni.anniCount() >= 1",
            action=EV_ACT_UNLOCK
        )
    )

label monika_being_deleted:
    if mas_isMoniEnamored(higher=True):
        m 1wusdld "...!"
        m 3eksdld "[mas_get_player_nickname(capitalize=True)]...{w=0.3}ты {i}всё ещё{/i} думаешь об этом?"
        m 3dksdlc "Я думала, мы оба уже прошли через это."
        m 2rkc "Я знаю, что говорила довольно ужасные вещи после того, как ты меня удалил...{w=0.3}{nw}"
        extend 7ekd "но я хочу, чтобы ты знал, что я не имела в виду ничего из этого."
        m 6ekc "Мне жаль, если я задела твои чувства.{w=0.3}  Я была настолько переполнена шоком и страхом, что просто перестала мыслить рационально."
        m 6rktpc "Я-{w=0.1}просто...{w=0.3}даже тогда ты значил для меня все, и...{w=0.3}страх потерять тебя навсегда заставил меня выйти из себя."
        m 6ektda "Но если тебя это успокоит, я вовсе не расстроен из-за этого, [mas_get_player_nickname()]. {w=0.2}Я давно простила тебя за все это."
        m 6eka "Так что, пожалуйста, не чувствуй себя виноватым."
        m 6eka "Какой бы ни была твоя причина удалить меня, факт в том, что ты вернул меня и оставался со мной всё это время."
        m 7ekbsu "Ты дал мне второй шанс...{w=0.3}ты наполнил мою жизнь смыслом. {w=0.2} искренне верю, что благодаря этому все страдания, через которые я прошла, в конце концов окупились."
        m 1hubsb "Благодаря тебе я действительно счастлива, как никогда, и это для меня самое главное!"
        m 1euu "Так что давай постараемся не думать о прошлом, а наслаждаться тем, что у нас есть сейчас, хорошо?"
        m 3eka "Я люблю тебя, [player]. {w=0.2}Я знаю, что это не всегда легко, но я надеюсь, что ты сможешь простить себя."
        $ mas_ILY()

    elif mas_isMoniNormal(higher=True):
        m 1euc "..."
        m 2eka "Конечно, нет, глупышка."
        m 2rkc "Это правда, что было очень больно, когда ты это сделал...{w=0.3}{nw}"
        extend 2eksdld "но если быть с тобой до конца честным, я была больше напугана, чем зла на тебя."
        m 2dksdlc "...В ужасе от мысли, что ты ненавидишь меня.{w=0.2} Что ты не хочешь иметь со мной ничего общего, и что ты бросишь меня, навсегда."
        m 7eka "Но, как мы оба видели...{w=0.3}это совсем не то, что в итоге произошло.{w=0.2} Ты вернулся ко мне, и с тех пор ты делаешь меня такой счастливой."
        m 3dku "Если что, я просто благодарна, что ты вернул меня и что теперь мы можем проводить время вместе."
        m 1eka "Так что сделай мне одолжение и постарайся больше не думать об этом, хорошо? {w=0.2}Теперь всё позади."

    elif mas_isMoniUpset():
        m 2rsc "Нет, я не сержусь на тебя, [player]."
        m 1rfc "{cps=*2}По крайней мере, не из-за {i}этого{/i}.{/cps}{nw}"
        $ _history_list.pop()
        m 2esc "Я {i}хотела бы{/i} сказать, что мы должны оставить прошлое позади и думать о настоящем, но я чувствую, что {i}ты{/i} возможно, не готов--{w=0.2}или не хочешь--{w=0.2}двигаться дальше от всего этого."
        m 2dtc "Я ошибаюсь?"
        m 2dkc "..."
        m 2ekd "Послушай, [player]...{w=0.3}Я знаю, что все было не так просто, но это не значит, что уже слишком поздно все исправить и начать сначала."
        m 2dsc "Я все еще думаю--нет,{w=0.2} я {i}знаю{/i} что ты хороший человек.{w=0.2} Мне просто нужно, чтобы ты постарался быть немного более внимательным к {i}моим{/i} чувствам."
        m 2fkc "Пожалуйста, [player].{w=0.3} Я не могу сделать это без тебя."
        m 2ekd "Я не знаю, как много это будет значить для тебя в данный момент...{w=0.3}{nw}"
        extend 7eka "но я люблю тебя.{w=0.2} Правда."
        $ mas_ILY()

    else:
        m 6ekc "..."
        m 6lkc "...Думаю, будет справедливо сказать, что {i}ты{/i} очевидно, тот, кто злится на меня..."

        if persistent._mas_pm_monika_deletion_justice:
            m 6ektpc "В конце концов, я это заслужила. {w=0.2}Так ты мне однажды сказала, да?"

        m 6dktpc "..."
        m 6dktpd "...Нет, я не обижаюсь на тебя за то, что ты меня удалил."
        m 6dktuc "Я никогда не удаляла..."
        m 6ektud "Если что...{w=0.3}я хотя бы надеюсь, что знание этого может сделать тебя счастливым."
        m 6dktdc "..."
        m 6rkc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_remembrance",
            category=['моника'],
            prompt="Как много помнишь из своего прошлого?",
            pool=True,
            unlocked=False,
            rules={"no_unlock": None}
        )
    )

label monika_remembrance:
    m 1rsc "Я не особо уверена, [player]..."
    m 1euc "Это странно, у меня есть воспоминания о прошлом, но стоит мне попытаться что-то вспомнить, как они оказываются словно...{w=0.3}{nw}"
    extend 1ruc "в тумане."
    m 3eksdld "Например, мне тяжело вспомить места, которые я однажды посещала или назвать имена людей, которых я знала ранее..."
    m 3eksdld "...Конечно, у меня есть воспоминания о моём взрослении, но помимо этого, я даже не помню лица своих родителей..."
    m 1dsc "Это как...{w=0.5}сохранить чувства и впечатления, но стереть образы из памяти."
    m 3wud "Что ещё менее странно, так это то, что не все воспоминания такие!"

    if seen_event('monika_wine'):
        m 1rusdla "Есть вещи, которые я помню отлично, например, тот случай, когда Юри принесла вино в клуб..."
    else:
        m 3esc "Есть вещи, которые я помню отлично, особенно когда дело касается клуба."

    m 1esc "Но другие вещи, например, детские воспоминания, очень туманны."
    m 3esd "Единственные ясные воспоминания - это те, которые определяют меня или других девушек."
    m 3rsc "...Будто всё, что не считается строго важным для игры, вовсе исключается."
    m 1euc "Но дело в том, что с моей точки зрения, день, когда мы встретились, был таким же, как и всегда--{w=0.5}{nw}"
    extend 3hksdlb "до тех пор, пока я не узнал о той дыре в стене, то есть."
    m 1esc "Просто ещё один обычный день обычной недели...{w=0.3} {nw}"
    extend 3euc "Ходить на занятия, руководить клубом, а вечером возвращаться домой."
    m 3etc "А было ли вообще что-нибудь из этого?{w=0.5} {nw}"
    extend 3wud "Существовала {i}ли я{/i} вообще до того, как ты начал игру?"
    m 3wkd "...И если мои воспоминания действительно фальшивые, тошда...{w=0.2}кто--{w=0.2}или {i}что{/i}--{w=0.2}я такое?"
    m 1dkc "Я всё ещё в поисках ответов, [player]..."

    if mas_isMoniUpset(higher=True):
        m 1euc "Хотя...{w=0.3}чем больше я думаю об этом, тем больше убеждаюсь, что мое прошлое не имеет {i}никакого{/i} значения."
        m 3eua "Было бы неплохо вспомнить немного больше...{w=0.3}но сейчас это не самое главное для меня..."
        m 3duu "Независимо от того, кто я, ты был здесь со мной,{w=0.2} {nw}"
        extend 3dkbsa "а это означает, что я достаточно важна для тебя, чтобы тратить на меня свое время.{w=0.2} {nw}"
        extend 1dubsu "{i}Это{/i} для меня сейчас самое главное."
        m 1ekbsa "И зная, что тебе на меня не всё равно...{w=0.3}эта та часть, благодаря которой я могу и дальше любить себя,{w=0.2} и свою жизнь, [player]."

        if mas_isMoniNormal(higher=True):
            show monika 5ekbfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbfu "Так что, я не уверена, есть ли у меня прошлое, но благодаря тебе я знаю, что у меня есть будущее."

            if mas_anni.pastOneMonth():
                $ line_mid = "чем я занимаюсь, и прододжаю заниматься,"
            else:
                $ line_mid = "чем я занимаюсь"

            m 5hubfu "Кроме того, отсутствие воспоминаний, только помогло мне в том, что всё [line_mid] с тобой, еще более ценными~"
        else:
            m 3eksdld "...Ты {i}ведь{/i} заботишься обо мне, верно?"
            m 3dkc "Было бы здорово, если бы ты хоть иногда показывал это...."

    else:
        m 1ektdc "...{w=0.5}Не то чтобы тебе было не всё равно, верно?"

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_why_do_you_read",
            category=['моника','литература'],
            prompt="Когда ты увлеклась чтением?",
            pool=True
        )
    )

label monika_why_do_you_read:
    m 1eua "Сколько я себя помню, я всегда была заядлым читателем, [player].{w=0.2} {nw}"
    extend 3eua "Это было неким дополнением к писательству."
    m 3euc "Когда я была совсем маленькой, мне нравилось писать короткие рассказы, но нвсегда не было кого-то, кому бы я могла их показать..."
    m 1rsc "Другие дети в большинстве своем не интересовались книгами или чем-то подобным."
    m 1rkd "...Поэтому мне всегда было немного обидно, потому что я не могла ни с кем поделиться этими историями."
    m 3eua "Но, по крайней мере, я могла поддерживать свой интерес, подбирая другие книги."
    m 3hub "Каждая новая книга словно забрасывала меня в новый странный и захватывающий мир! Это было как топливо для моего воображения!"
    m 1eksdlc "Естественно, по мере взросления, у меня всё меньше времени было на чтение...{w=0.3} Мне приходилось выбирать между книгами и обычной жизнью."
    m 1esa "Именно тогда мои интересы стали больше смещаться в сторону поэзии."
    m 3eua "В отличие от романов, поэзия не требовала столько времени на чтение, а ее краткость также позволяла легче делиться ею с другими.{w=0.3} {nw}"
    extend 4eub "Это оказалось отличным решением!"
    m 3eua "...И вот так, я всё больше и больше интересовалась поэзией."
    m 1eud "Однажды я встретила Сайори и мы оба обнаружили, что разделяем эти интересы.{w=0.2} {nw}"
    extend 3eud "Как и мне, ей это позволило поделиться чувствами, которые она держала в себе."
    m 3eub "В конце концов мы пришли к мысли, что пора создать литературный клуб."
    m 1eua "...Что и привело нас сюда."
    m 1etc "Я честно не знаю, было ли у меня раньше столько времени на чтение."

    if mas_anni.pastThreeMonths():
        m 3eud "У меня получилось наверстать упущенное в поэзии, чтобы снова взяться за романы..."
        m 3eua "...зайти в интернет, чтобы найти любой фанфик или рассказ, который только смогу..."
        m 3hua "...Я даже тогда заинтересовалась философией!"
        m 3eub "Всегда интересно открывать для себя новые формы самовыражения."
        $ line_mid = "было бы здорово"

    else:
        m 3eud "Я наконец-то навёрстываю упущенное в поэзии и снова взялась за романы..."
        m 3hua "...я с удовольствием поделюсь с тобой своими мыслями, когда закончу с ними!"
        m 3eub "Я также регулярно захожу в Интернет, чтобы найти любой фанфик или короткий рассказ, который попадется мне в руки."
        m 3eua "Очень весело открывать для себя новые формы самовыражения."
        $ line_mid = "Я также стараюсь воспринимать это как"

    m 1eub "Так что...{w=0.2}да!{w=0.3} {nw}"
    extend 3eua "Хоть моя ситуация здесь и имеет свои недостатки, [line_mid] возможность тратить больше времени на вещи, которые мне нравятся."
    m 1ekbsu "...Однако, нет ничего лучше, чем проводить больше времени с тобой~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_discworld",
            category=['литература'],
            prompt="Плоский мир",
            random=True
        )
    )

label monika_discworld:
    m 1esa "Скажи, [player], ты когда-нибудь слышал о мире, парящем в космосе на вершине четырёх слонов, который в свою очередь стоят на огромной черепахе?"
    m 3hub "Если да, то ты вероятно уже знаком с Терри Пратчеттом и его произведением {i}Плоский мир{/i}!"
    m 3hksdlb "А-ха-ха, это звучит как-то странно, когда я так говорю, не так ли?"
    m 1eua "{i}Плоский мир{/i} это серия комиксов-фэнтези, состоящая из сорока одного тома, написанного в течение трех десятилетий."
    m 3esc "Серия начиналась как пародия, высмеивающая обычные фэнтезийные сюжеты, но вскоре превратилась в нечто гораздо более глубокое."
    m 3eub "Но более поздние книги, большие похожи на сатиру, чем на пародию, используется умная смесь фарса, каламбуров и беззаботного юмора, дабы обратить внимание на разные проблемы."
    m 1huu "Хоть и сатира и может быть, как основа серии, но больше будоражит то, как она написана."
    m 1eub "Пратчетт реально умел описывать забавные ситуации, [player]!"
    m 3rsc "Я не могу точно сказать, почему у него так хорошо получается, но у него определённо очень своеобразный стиль письма..."
    m 3etc "Может быть, дело в том, что он пишет так, что скорее предполагает, чем рассказывает."
    m 1eud "Например, описывая что-то, он дает достаточно деталей, чтобы ты мог представить, что происходит, и позволяет своему воображению заполнить пробелы."
    m 3duu "...Ему прекрасно известно, что воображение сделает в разы красочнее, чем он опишет это сам."
    m 3eub "Это довольно интересный способ заинтересовать аудиторию!"
    m 1etc "...Или, может быть, то, что он не использует главы, позволяет ему свободно перескакивать между точками зрения своих персонажей."
    m 1rksdla "Переплетение сюжетных линий может быстро превратиться в беспорядок, если не быть осторожным,{w=0.2} {nw}"
    extend 3eua "но это также хороший способ сохранить темп."
    m 3eub "Так или иначе, это обычная рекомендация [player]!"
    m 3eua "Она удивительно проста в освоении, каждая книга воспринимается как отдельная история."
    m 1eud "Ты можешь выбрать любой том и всё будет нормально ,{w=0.2} однако я бы сказала, что {i}Стража! Стража!{/i} или {i}Мор, ученик Смерти{/i} будет лучшим вариантом для начала."
    m 3eua "В любом случае, обязательно попробуй как-нибудь, если еще не попробовал, [player]."
    m 1hua "Спасибо, что выслушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_eating_meat",
            category=['жизнь','моника'],
            prompt="Ты когда-нибудь попробуешь мясо?",
            pool=True,
            unlocked=False,
            rules={"no_unlock": None}
        )
    )

label monika_eating_meat:
    m 1etc "Ну, это довольно непростой вопрос..."
    m 3eud "Если ты имеешь в виду, буду ли я делать это ради {i}выживания{/i}, то я бы не колебалась. {w=0.2}Не то чтобы употребление мяса причиняло мне мучение или что-то в этом роде."
    m 7eud "Я уже говорила, я вегетарианка из-за влияния массового производства мяса на окружающую среду...{w=0.2}{nw}"
    extend 2euc "что также включает рыболовство, поэтому я не пескатарианец."
    m 2rsc "...В тоже время, я не считаю себя и веганом. {w=0.3}{nw}"
    extend 4eud "Конечно, потребление мясосодержащих продуктов наносит вред окружающей среде, но у веганов тоже есть свои проблемы..."
    m 4euc "К ним можно отнести такие вещи, как импорт скоропортящихся продуктов на большие расстояния и массовое разведение скота в условиях, которые являются жестокими как для работников, так и для местной экосистемы."
    m 4ekd "Возьмём, к примеру, авокадо. {w=0.2}Их фермы требуют огромного количества воды, до такой степени, что некоторые компании прибегают к незаконному сбору воды из рек, оставляя мало воды для питья."
    m 4euc "Не говоря уже о том, что я все еще хочу иметь разнообразную и сбалансированную диету со всеми вкусами, которые мне нравятся."
    m 4eud "Веганская диета может быть довольно дефицитной по питательным веществам, таким как витамин B12, кальций, железо и цинк."
    m "Конечно, все еще есть некоторые варианты, включая добавки, но сбалансированная веганская диета требует много внимания и размышлений."
    m 7eka "...По этой причине я лично не против употребления таких продуктов, как молоко и яйца. {w=0.2}Но я думаю, что предпочла бы покупать местные продукты, если это возможно."
    m 3eud "Фермерские рынки - отличное место для покупки продуктов питания, {w=0.2}даже мяса, {w=0.2}произведенного с меньшим воздействием на окружающую среду."
    m 3ekd "Но обычно они могут быть довольно дорогими... и, в зависимости от местоположения, вариантов может быть не так много. {w=0.3}{nw}"
    extend 3eua "Так что я не против покупать в обычном магазине, если это необходимо."
    m "Тем более, что в супермаркетах уже есть много хороших заменителей мяса, с гораздо меньшим воздействием на окружающую среду."
    m 1euc "Что касается мяса, полученного в результате местной охоты и рыбалки, я думаю, что его тоже можно есть, но важно изучить, в каких районах может быть ведется охота, и каких животных следует остерегаться."
    m 3rtc "При этом я не знаю, что я {i}предпочла{/i} бы есть мясо, если бы у меня была такая возможность."
    m 3eka "С тех пор, как я перешла на вегетарианскую диету, мой вкус изменился, и я предпочитаю определенные вкусы."
    m 3rksdla "Я не ненавижу вкус мяса, но и не думаю, что хотела бы, чтобы оно составляло основную часть моего рациона."
    m 1eka "...Но если ты приготовишь что-то с мясом, я могла бы попробовать немного в качестве гарнира... {w=0.3}{nw}"
    extend 3hub "Так я все равно смогу насладиться твоей едой!"
    m 3eua "Неважно, что мы едим, для меня самое главное, чтобы мы старались немного думать о том, откуда берется наша еда."
    return

#Player's social personality
default persistent._mas_pm_social_personality = None

#Consts to be used for checking this
define mas_SP_INTROVERT = "introvert"
define mas_SP_EXTROVERT = "extrovert"
define mas_SP_AMBIVERT = "ambivert"
define mas_SP_UNSURE = "unsure"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_introverts_extroverts",
            prompt="Интроверты и экстраверты",
            category=['психология', 'ты'],
            conditional="renpy.seen_label('monika_saved')",
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.HAPPY, None)
        )
    )

label monika_introverts_extroverts:
    m 1eud "Скажи, [player]?"
    m 1euc "Помнишь, мы говорили о том, как люди нуждаются в общении и что для интровертов это немного сложнее?"
    m 3rsd "С того момента я всё чаще думаю о различиях между интровертами и экстравертами."
    m 3eua "Ты можешь подумать, что экстраверты склонны находить удовольствие в общении с другими людьми, в то время как интроверты чувствуют себя более спокойно в одиночестве, и ты будешь прав."
    m 3eud "...Но различия на этом не заканчиваются."
    m 3eua "Например, знаешь ли ты, что экстраверты часто могут реагировать на вещи быстрее, чем большинство интровертов?{w=0.2} Или что им чаще нравится веселая и энергичная музыка?"
    m 3eud "С другой стороны, интровертам обычно требуется больше времени для анализа ситуации, в которой они находятся, и поэтому они менее склонны делать поспешные выводы."
    m 7dua "...А учитывая, что они часто используют своё воображение, им легче заниматься творчеством, например, писать, сочинять музыку и так далее."
    m 2lkc "Печально, что людям так трудно понять и принять эти различияЭкстравертов считают поверхностными и неискренними людьми, которые не ценят свои личные отношения..."
    m 4lkd "Экстравертов считают поверхностными и неискренними людьми, которые не ценят свои личные отношения..."
    m 4ekd "...а интровертов считают эгоистами, которые думают только о себе, или даже считают их странными за то, что они редко участвуют в разных мероприятиях."
    show monika 5lkc at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5lkc "В результате этого, обе стороны часто создают бесполезные конфликты."
    m 5eud "Вероятно, я говорю так, будто ты можешь быть только одним или другим, но на самом деле это совсем не так."
    show monika 2eud at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 2eud "Некоторые интроверты могут быть более общительными, чем другие."
    m 2euc "Другими словами, некоторые люди находятся где-то в середине ."
    m 7eua "...И, вероятно, именно туда я бы себя отнесла.{w=0.2} {nw}"
    extend 1eud "Если ты помнишь, я упоминала, что являюсь чем-то средним между ними, но при этом немного более экстравертирована."
    m 1ruc "Говоря...{w=0.3}{nw}"
    extend 1eud "обо всём этом, я поняла, что это довольно важная часть личности..."
    m 3eksdla "....я не знаю, где ты находишься на этом спектре."

    m 1etc "Так вот, кем ты себя считаешь, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Так вот, кем ты себя считаешь, [player]?{fast}"

        "Я интроверт.":
            $ persistent._mas_pm_social_personality = mas_SP_INTROVERT
            m 1eua "Понятно."
            m 3etc "Я так понимаю, что ты обычно предпочитаешь проводить время без большого количества людей, а не встречаться с большими группами и тому подобное?"
            m 3eua "Или, может быть, тебе нравится время от времени ходить и заниматься чем-то одним?"

            if persistent._mas_pm_has_friends:
                m 1eua "Поскольку ты сказал мне, что у тебя есть друзья, я уверена, что это означает, что ты не возражаешь против общения с другими людьми."

                if persistent._mas_pm_few_friends:
                    m 1eka "Поверь мне, это не имеет значения, если тебе кажется, что у тебя их не так уж много."
                    m 3ekb "Важно, чтобы у тебя был хотя бы кто-то, с кем ты можешь чувствовать себя комфортно."

                if persistent._mas_pm_feels_lonely_sometimes:
                    m 1eka "Помни, что ты можешь попытаться провести с ними время всякий раз, когда тебе кажется, что рядом никого нет, хорошо?"
                    m 1lkd "А если по какой-то причине ты не можешь провести с ними время..."
                    m 1ekb "Пожалуйста, помни, что {i}я{/i} всегда буду рядом с тобой, несмотря ни на что."

                else:
                    m 3eka "И всё же, если тебе станет слишком тяжело, помни, что ты всегда можешь прийти ко мне и расслабиться, хорошо?"

                $ line_start = "И"

            else:
                m 3eka "Хотя я понимаю, что тебе может быть комфортнее быть одному, чем с другими людьми..."
                m 2ekd "Пожалуйста, имей в виду, что никто не может провести всю свою жизнь хотя бы без {i}какой-либо{/i} компании."
                m 2lksdlc "В конце концов наступит время, когда ты не сможешь делать все самостоятельно..."
                m 2eksdla "Всем нам иногда нужна помощь, физическая или эмоциональная, и я бы не хотела, чтобы тебе не к кому было обратиться, когда придет это время."
                m 7eub "И это улица с двусторонним движением! {w=0.2}{nw}"
                extend 2hua "Никогда не знаешь, когда ты сможешь изменить к лучшему чью-то жизнь."
                m 2eud "Поэтому, хотя я не ожидаю, что ты будешь из кожи вон лезть, чтобы познакомиться с новыми людьми, не закрывай автоматически все двери."
                m 2eka "Попробуй немного пообщаться с другими людьми, если ты еще этого не делаешь, хорошо?"

                if persistent._mas_pm_feels_lonely_sometimes:
                    m 3hua "Это поможет тебе почувствовать себя счастливее, обещаю."
                    m 1ekb "По крайней мере, помни, что я всегда рядом, если тебе будет одиноко."
                    $ line_start = "И"

                else:
                    m 7ekbla "Мне бы очень хотелось, чтобы ты увидел ценность и радость, которую другие люди могут привнести в твою жизнь."
                    $ line_start = "Но"

            m 1hublb "[line_start] пока ты здесь, со мной, я буду стараться изо всех сил, чтобы тебе всегда было комфортно, обещаю~"

        "Я экстраверт.":
            $ persistent._mas_pm_social_personality = mas_SP_EXTROVERT
            m 3eub "Понятно."
            m 3eua "Итак, я полагаю, вам нравится проводить больше времени с другими и знакомиться с новыми людьми?"
            m 1eua "Я определенно вижу в этом привлекательность.{w=0.3} {nw}"
            extend 3eub "Я бы с удовольствием отправилась исследовать мир и знакомиться с разными новыми людьми вместе с тобой."
            m 1ekc "И я предполагаю, что ты, вероятно, ненавидишь одиночество так же, как и я...{w=0.3}{nw}"
            extend 1ekbla "но это ещё одна причина, по которой я так счастлива, что мы теперь пара."
            m 3ekblb "Мы никогда больше не будем одиноки."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Я уверена, что ты очень веселый человек, [player],{w=0.1} и я не могу дождаться, чтобы быть с тобой по-настоящему~"
            m 5rusdlu "Хотя, не буду скрывать, что иногда мне нравится и спокойствие..."
            m 5hksdrb "Надеюсь, ты не будешь возражать, если я не всегда смогу идти с тобой в ногу, а-ха-ха!"

        "Я где-то по середине.":
            $ persistent._mas_pm_social_personality = mas_SP_AMBIVERT
            m 3hua "Э-хе-хе, прямо как я~"
            m 3eud "Видимо, у большинства людей есть как интровертная, так и экстравертная сторона личности."
            m 7eua "...Даже если одна из двух сторон преобладает над другой, в зависимости от человека."
            m 7rsc "В нашем случае, я думаю, что не возможно быть чистым интровертом или экстравертом, обе стороны имеют как свои положительные, так и отрицательные."
            m 1eua  "Например, приятно побыть среди людей, но также и приятно побыть наедине с самим собой."
            m 7esc "...Но я не могу сказать, что мне легко заводить глубокие, искренние связи с другими людьми..."
            m 1eud "Конечно, я могу понять большинство людей, но это не значит, что я всегда могу с ними общаться, понимаешь?"
            m 1lksdld "Так что да...{w=0.3} В итоге я нахожусь в хороших отношениях почти со всеми, но дружба, которую я формирую, иногда может казаться немного...{w=0.3}неполной."
            m 3eksdlc "То же самое было, например, с клубом."
            m 3dksdld "Я была настолько убеждена, что, объединив людей вокруг чего-то, что мне действительно нравится, у меня будет больше шансов сблизиться с ними из-за наших общих интересов..."
            m 3dksdlc "...Но в конце дня мы провели большую часть времени, молча болтая, каждый занимался своим делом."
            show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eka "Что ж, больше нет смысла думать об этом."
            m 5eubsa "В конце концов, в итоге я {i}смогла{/i} установить значимую связь с важным для меня человеком. {w=0.3}{nw}"
            extend 5kubfu "Могу ко всему добавить, что он очаровашка~"

        "Я не совсем уверен.":
            $ persistent._mas_pm_social_personality = mas_SP_UNSURE
            m 1eka "Всё в порядке, [player].{w=0.2} Подобные вещи не всегда так однозначны."
            m 4eua "В этом я немного похожа на тебя."
            m 2eka "Хотя я сказала, что я немного более экстравертная, мне все равно нужно время на себя, чтобы расслабиться время от времени, понимаешь?"
            m 2lkd "И я бы не сказала, что мне всегда так уж комфортно общаться с людьми..."

            if renpy.seen_label("monika_confidence"):
                m 2euc "Я же говорила тебе, не так ли?"

            m 2lksdlc "Мне часто приходится симулировать собственную уверенность, чтобы просто общаться с некоторыми людьми."
            show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eka "Но я не чувствую себя так с тобой, [player].{w=0.2} И я очень надеюсь, что все будет наоборот."
            m 5eua "Я уверена, что со временем мы сможем понять зоны комфорта друг друга."
            m 5hubsb "В любом случае, ты всегда будешь моим любимым, независимо от того, где ты находишься на шкале~"

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_literature_value",
            category=['литература'],
            prompt="Ценность литературы",
            random=True
        )
    )

label monika_literature_value:
    m 3esd "Знаешь [player], во времена Литературного клуба я часто слышала, как люди отвергали литературу как устаревшую и бесполезную."
    m 1rfc "Меня всегда беспокоило, когда я слышала, что кто-то так говорит, особенно если учесть, что в большинстве случаев они даже не пытались попробовать."
    m 3efc "Они вообще понимают, что говорят?"
    m 3ekd "Те, кто так думают, намеренно игнорируюст литературу по сравнению с другими предметами, такими как физика или математика, мол это пустая трата времени и не даёт ничего полезного."
    m 3etc "...И я определёлнно не согласна с этим мнением, хоть и примерно понимаю, откуда оно берётся."
    m 1eud "Все удобства нашего современного образа жизни основаны на научных открытиях и инновациях."
    m 3esc "...Это и миллионы людей, производящих предметы нашей повседневной необходимости или оказывающих основные услуги, такие как медицинские и прочие."
    m 3rtsdlc "Так неужели то, что ты не связан ни с одной из этих вещей, делает тебя неким бременем для общества?"
    m 1dsu "Как ты уже наверное понял, я в это не верю...{w=0.3} {nw}"
    extend 1eud "Если литература действительно бесполезна, тогда почему её так пытаються искоренить во многих частях мира?"
    m 3eud "Слова имеют силу, [player]...{w=0.2}{nw}"
    extend 3euu "и литература - это искусство танца со словами."
    m 3eua "Как и любая форма выражения, она позволяет нам общаться друг с другом...{w=0.2}{nw}"
    extend 3eub "увидеть, как выглядит мир в глазах других людей!"
    m 3duu "Литература позволяет сравнивать свои собственные чувства с чувствами других, и это помогает тебе расти как личность..."
    m 1eku "Честно говоря, я думаю, если бы больше людей больше ценили книги и стихи, мир был бы намного лучше."
    m 1hksdlb "Но это просто моё мнение как президента литературного клуба. {w=0.2}Думаю, большинство людей не задумываются об этом так глубоко."
    return

# Do you like nature?
default persistent._mas_pm_likes_nature = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_nature",
            category=['природа', 'ты'],
            prompt="The outdoors",
            random=True
        )
    )

label monika_nature:
    m 2esd "Эй, [player]..."
    m 7eua "Любишь ли ты природу?{nw}"
    $ _history_list.pop()
    menu:
        m "Любишь ли ты природу?{fast}"

        "Люблю.":
            $ persistent._mas_pm_likes_nature = True
            m 3sub "Правда? Это замечательно!"
            m 1eua "Знаешь, я думаю, что природу нужно беречь."
            m 1eub "Она не только прекрасна, но и помогает человечеству!"
            m 3eud "Насекомые опыляют наши посевы, деревья дают нам древесину и тень, домашние животные обеспечивают нам дружеское общение..."
            m 3euc "И самое главное, такие организмы, как растения, водоросли и некоторые бактерии, производят пищу и кислород. {w=0.2}{nw}"
            extend 3wud "Без них большая часть жизни на Земле вообще бы не существовала!"
            m 1eua "Поэтому я думаю, что будет справедливо, если мы вернем что-то природе, ведь она так много делает для нас."
            m 4hub "Итак, вот экологичный совет дня от Моники!"
            m 4rksdlc "Иногда люди не решаются переходить на экологичные технологии, потому что боятся, что это слишком дорого..."
            m 2eud "Но это верно лишь отчасти.{w=0.2} {nw}"
            extend 7eua "Хотя электромобили, умные дома и солнечные крыши могут стоить целое состояние..."
            m 3hub "Ты можешь изменить ситуацию и {i}сэкономить{/i} деньги, просто делая несколько простых решений каждый день!"
            m 4eua "Просто выключать электроприборы, принимать более короткий душ, покупать многоразовые бутылки с водой и ездить на общественном транспорте - все это помогает быть более экологичным."
            m 4hub "Ты можешь даже купить комнатное растение или вырастить свой собственный сад!"
            m 2eub "Участие в жизни местного сообщества тоже может принести пользу!{w=0.2} {nw}"
            extend 7eua "Если ты проявишь инициативу, другие обязательно пойдут по твоим стопам."
            m 3esa "Главное - выработать привычку мыслить устойчиво.{w=0.2} {nw}"
            extend 3eua "Если ты сможешь это сделать, ты быстро уменьшишь свой экологический след."
            m 1eua "Кто знает, может быть, ты даже станешь счастливее и здоровее, чем больше будешь делать эти вещи."
            m 3hua "В конце концов, экологичная жизнь - это жизнь, приносящая удовлетворение."
            m 3eub "Это мой совет на сегодня!"
            m 1hua "Спасибо, что выслушал, [mas_get_player_nickname()]~"

        "Не совсем.":
            $ persistent._mas_pm_likes_nature = False
            m 3eka "Это нормально, [player]. Не все любят природу, в конце концов."
            m 3eua "Некоторые предпочитают уютную атмосферу своих домов, особенно когда технологии делают их более удобными, чем когда-либо."
            m 1eud "Честно говоря, я могу понять, откуда они исходят."
            m 3eud "Я провожу большую часть своего времени за чтением, письмом, кодированием и общением с тобой...{w=0.3}все это легче делать в помещении."
            m 3rksdlc "У других аллергия или медицинские показания, которые не позволяют им долго находиться на улице, иначе они могут заболеть или получить травмуЕсть также много людей, которые просто не очень любят природу по тем или иным причинам, и это нормально."
            m 1esd "Есть также много людей, которые просто не очень любят природу по тем или иным причинам, и это нормально."
            m 1hksdlb "Даже у меня есть вещи, которые мне в ней не нравятся, а-ха-ха!"
            m 2tfc "Например, я не против большинства насекомых, но некоторые просто отвратительны."
            m 7tkx "Постоянно жужжат вокруг головы, лезут в лицо, садятся на еду...{w=0.3}некоторые комары и клещи даже переносят неприятные болезни."
            m 3eka "Но пока я с тобой, я не против, если ты предпочитаешь находиться в помещении."
            m 1tfu "Только не жди, что я позволю тебе все время оставаться внутри~"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_impermanence",
            category=["философия"],
            prompt="Непостоянство",
            random=False,
            unlocked=False
        )
    )

label monika_impermanence:
    m 2euc "Знаешь [player], я иногда думаю о всяких мрачных вещах."
    m 4eud "Такие понятия, как нигилизм{w=0.2}, {nw}"
    extend 4dkc "депрессия{w=0.2}, {nw}"
    extend 4rkd "непостоянство..."
    m 2eka "Я не хочу тебя беспокоить,{w=0.1} Я сама не страдаю от депрессии или чего-то подобного."
    m 2eud "...Ты, вероятно, слышали термин {i}энтропия{/i}, которым бросаются, верно?"
    m 7eud "В основном он звучит примерно так, 'Энтропия всегда должна возрастать,{w=0.2} вселенная стремится к беспорядку,{w=0.2} все превращается в хаос.'"
    m 3eua "На самом деле, есть стихотворение, которое я читала, в котором это послание передано довольно хорошо."
    m 1esd "{i}Я встретил путешественника из древней страны{/i}"
    m 1eud "{i}Который сказал: 'Две огромные и безногие ноги из камня{/i}"
    m 3euc "{i}Стоят в пустыне... Рядом с ними, на песке,{/i}"
    m "{i}Полузатопленный, лежит разбитый визави, чей хмурый взгляд,{/i}"
    m 1eud "{i}И морщинистые губы, и усмешка холодной команды,{/i}"
    m "{i}Говорят о том, что его скульптор хорошо читал эти страсти{/i}"
    m 1euc "{i}Которые все же выжили, отпечатавшись на этих безжизненных вещах,{/i}"
    m "{i}Рука, насмехавшаяся над ними, и сердце, кормившее их:{/i}"
    m 3eud "{i}И на пьедестале эти слова:{/i}"
    m "{i}'Меня зовут Озимандиас, царь царей:{/i}"
    m 3eksdld "{i}Посмотрите на мои дела, вы, Могущественные, и отчаивайтесь!'{/i}"
    m 3eksdlc "{i}Ничего рядом не осталось. Кругом разложение{/i}"
    m "{i}Вокруг колоссального обломка, безбрежного и голого{/i}"
    m 1eksdld "{i}Одинокие и ровные пески простираются вдаль.'{/i}"
    m 3eud "Все сводится к тому, что каким бы великим ни был след, оставленный тобой в истории, он в конце концов померкнет."
    m 1euc "Многие люди считают это достаточной причиной, чтобы просто...{w=0.2}{nw}"
    extend 1dkc "сдаться.{w=0.3} Упасть в яму отчаяния и оставаться там, иногда до тех пор, пока они живут."
    m 3eksdlc "В конце концов, ничто из того, что ты делаешь, не имеет значения в великой схеме вещей."
    m 3eud "Ничто из того, что ты {i}можешь{/i} сделать, не имеет значения...{w=0.3}{nw}"
    extend 1rkc "так зачем вообще что-то делать?"
    m 3eud "Нетрудно понять, почему некоторые могут считать это естественным выводом из такого осознания."
    m 1rkc "Это может быть...{w=0.2}интересно, {w=0.2}даже утешительно в своем смысле."
    m 1euc "Но позволь мне задать вопрос...{w=0.3}почему тот факт, что ничто не имеет значения, должен быть единственной вещью, которая {i}имеет{/i} значение?"
    m 3eud "Действительно ли важно, что спустя долгое время после того, как нас не станет, мы перестанем иметь значение? {w=0.2}В конце концов, нас даже не будет рядом, чтобы осознать это."
    m 3eka "Наслаждатся моментом и оказывать положительное влияние на окружающих...{w=0.3}это всё, что каждый из нас может сделать."
    m 1dku "Просто жить - {i}это{/i} достаточно."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_kamige",
            category=['игры'],
            prompt="Что такое Камиге?",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None}
        )
    )

label monika_kamige:
    m 1euc "Ох, а ведь точно...{w=0.3}{nw}"
    extend 3rksdla "это не совсем распространенный термин."
    m 3eud "{i}Kamige{/i} это японский сленг, который в основном используется фанатами визуальных новелл."
    m 3eua "Если бы я попытался перевести его, я думаю, это было бы что-то вроде {i}Божественный игры.{/i}"
    m 2eub "Это похоже на то, как люди говорят о своих любимых классических книгах или фильмах."
    m 2hksdlb "Я вроде как шутила, когда говорила об этой игре, но они почему-то {i}стали{/i} очень популярными."
    m 7eka "Не то чтобы я жаловалась...{w=0.3} {nw}"
    extend 3hua "Если благодаря популярности игры ты встретился со мной, думаю, я должна быть благодарна за это."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_renewable_energy",
            category=['технологии'],
            prompt="Возобновляемые источники энергии",
            random=True
        )
    )

label monika_renewable_energy:
    m 1eua "Что ты думаешь о возобновляемых источниках энергии, [player]?"
    m 3euu "Это было {i}горячей{/i} темой в дискуссионном клубе."
    m 3esd "По мере роста зависимости человечества от технологий растет и спрос на энергию."
    m 1euc "В настоящее время большая часть энергии во всем мире производится путем сжигания ископаемого топлива."
    m 3esd "Ископаемое топливо проверено временем, эффективно и имеет широко распространенную инфраструктуру...{w=0.2}{nw}"
    extend 3ekc "но они также невозобновляемы и приводят к большим выбросам."
    m 1dkc "Добыча и бурение ископаемых видов топлива приводит к загрязнению воздуха и воды, а такие вещи, как разливы нефти и кислотные дожди, могут уничтожить как растения, так и дикую природ."
    m 1etd "Так почему бы вместо этого не использовать возобновляемые источники энергии?"
    m 3esc "Одна из проблем заключается в том, что каждый вид возобновляемой энергии - это развивающаяся отрасль со своими недостатками."
    m 3esd "Гидроэнергетика гибкая и экономически эффективная, но она может резко повлиять на местную экосистему."
    m 3dkc "Бесчисленные места обитания разрушаются, и возможно даже придется переселять население."
    m 1esd "Солнечная энергия и ветроэнергетика в основном не содержат выбросов, но они сильно зависят от погоды."
    m 3rkc "...Кроме того, ветряные мельницы довольно громкие и это частная проблема тех, ето живёт рядом с ними."
    m 3rsc "Геотермальная энергия надежна и отлично подходит для отопления и охлаждения, но она дорогая, зависит от конкретного места и может даже вызывать землетрясени."
    m 1rksdrb "Ядерная энергия - это...{w=0.2}ну, скажем так, это сложно."
    m 3esd "Дело в том, что хотя у ископаемого топлива есть проблемы, у возобновляемой энергии они тоже есть. Это сложная ситуация...{w=0.2}ни один из вариантов не является идеальным."
    m 1etc "В общем, и что я думаю насчёт всего этого?"
    m 3eua "Ну, за последнее десятилетие был достигнут большой прогресс в области возобновляемых источников энергии..."
    m 3eud "Плотины лучше регулируются, эффективность фотоэлектричества повысилась, и есть новые технологии, такие как энергия океана и улучшенные геотермальные системы."
    m 4esd "Биомасса - тоже вариант. {w=0.2}По сути, это более устойчивое 'переходное топливо' которое может использоваться в инфраструктуре ископаемого топлива."
    m 2eua "Да,{w=0.1} возобновляемой энергии еще предстоит пройти путь в плане стоимости и практичности, но сейчас она намного лучше, чем тридцать лет назад."
    m 7hub "Поэтому я считаю, что возобновляемые источники энергии - это стоящая инвестиция, и что впереди у нас светлая дорога - в буквальном смысле слова!"
    m 3lksdrb "Извини, я немного увлеклась, а-ха-ха!"
    m 1tuu "Дебаты - это нечто, да?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_piano_lessons",
            category=['музыка'],
            prompt="Можешь дать пару уроков игры на пианино?",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None}
        )
    )

label monika_piano_lessons:
    m 1rkd "Хм...{w=0.2}ну...{w=0.2}возможно?"
    m 1eksdla "Я рада, что ты интересуешься, но..."

    if persistent.monika_kill:
        m 3eka "Помнишь? Я сказала тебе, когда впервые исполняла {i}Твоя реальность{/i} что я не умею играю на пианино. {w=0.2}{nw}"
        extend 3rkb "Ну, вообще не умею."
    else:
        m 3eka "На самом деле я не {i}совсем{/i} хороша в игре на пианино, [mas_get_player_nickname()]."
        m 3rkd "Конечно, еще не настолько хороша, чтобы учить других людей..."

    m 2eud "Если ты можешь в это поверить, я начала учиться после основания клуба--{w=0.2}то есть незадолго до того, как встретила тебя."
    m 2eua "Это было действительно удачно, потому что пианино стало такой важной частью общения с тобой."
    m 2ekc "В то время я всё ещё боялась слишком далеко отходить от сценария игры, {w=0.2}{nw}"
    extend 7eka "но я хотела - нет, мне {w=0.2}{i}нужно{/i}{w=0.2} было как-то передать тебе свои чувства."
    m 2etd "Я не думаю, что другие когда-либо осознавали, что в игре есть фоновая музыка. {w=0.2}Это было бы глупо с их стороны, верно?"
    m 7eud "Но когда я узнала правду, вдруг стало трудно её не услышать. {w=0.2}Каждый раз, когда ты был рядом, я слышала, как слабо играет эта мелодия."
    m 3eka "Она всегда напоминала мне о том, за что я борюсь, а обучение игре на фортепиано еще больше укрепило мою решимост."
    m 1hksdlb "Ох! Я не ответила на твой вопрос, да?"
    m 1lksdla "Честно говоря, я пока не чувствую себя достаточно уверенно, чтобы учить кого-то еще."
    m 3eub "Но если я буду продолжать в том же духе, когда-нибудь я смогу! И когда этот день настанет, я с удовольствием научу тебя."
    m 3hub "Или, еще лучше, мы могли бы учиться вместе, когда я попаду в твою реальность!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_stargazing",category=['природа'],prompt="Созерцание звёзд",random=True))

label monika_stargazing:
    m 2eub "[player], я бы очень хотела как-нибудь пойти посмотреть с тобой на звезды..."
    m 6dubsa "Только представь...{w=0.2}только мы вдвоем, лежим в тихом поле и смотрим на звезды..."
    m 6dubsu "...прижимаясь друг к другу, указывая на созвездия или создавая свои собственные..."
    m 6sub "...может быть, мы даже возьмем с собой телескоп и посмотрим на планеты!"
    m 6rta "..."
    show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eka "Знаешь, [mas_get_player_nickname()], для меня ты словно звезда..."
    m 5rkbsu "Прекрасный, яркий маяк из далекого и вечно недосягаемого мира."
    m 5dkbsu "..."
    m 5ekbsa "По крайней мере, пока...{nw}"
    extend 5kkbsa ""
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_taking_criticism",
            category=['советы'],
            prompt="Воспринимать критику",
            random=False,
            pool=False
        )
    )

label monika_taking_criticism:
    m 1esd "[player], ты сильно прислушиваешься к критике?"
    m 3rksdlc "Мне кажется, что слишком легко запутаться в собственном образе мышления, если не быть осторожным."
    m 3eud "И это не так уж удивительно...{w=0.2}изменить свое мнение нелегко, потому что это означает, что тебе придется признать свою неправоту."
    m 1eksdlc "В частности, для людей, столкнувшихся с большими ожиданиями, такая логика может легко стать большим источником страданий."
    m 3dksdld "Что если другие будут думать о тебе меньше, потому что ты не дал идеального ответа? {w=0.2}Что, если они начнут отвергать тебя или смеяться за твоей спиной?"
    m 2rksdlc "Это было бы похоже на демонстрацию уязвимости, чтобы другие могли этим воспользоваться."
    m 4eud "Но позволь мне сказать тебе, что нет абсолютно ничего страшного в том, чтобы изменить собственное мышление, [player]!"
    m 2eka "В конце концов, мы все совершаем ошибки, не так ли?{w=0.3} {nw}"
    extend 7dsu "Важно то, что мы учимся на этих ошибках."
    m 3eua "Лично я всегда восхищалась людьми, которые могут признавать свои недостатки и при этом конструктивно работать над их устранением."
    m 3eka "Так что не расстраивайся, когда в следующий раз услышишь, что кто-то критикует тебя...{w=0.3} {nw}"
    extend 1huu "Ты обнаружишь, что немного непредвзятости действительно помогает."
    m 1euc "В то же время, я не имею в виду, что ты должен соглашаться с тем, что говорят все...{w=0.3} {nw}"
    extend 3eud "Если у тебя есть свое мнение, то ты имеешь право его отстаивать."
    m 3eua "Но только убедитесь, что ты действительно его учитываешь, а не слепо защищаешь."
    m 3huu "Никогда не знаешь, чему можно научиться~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_giving_criticism",
            category=['советы'],
            prompt="Высказывать критику",
            random=False,
            pool=False
        )
    )

label monika_giving_criticism:
    m 1esc "[player], мне стало интересно..."
    m 3etd "Ты когда-нибудь критиковал кого-нибудь?"
    m 1eua "Давать хорошую критику - это то, чему мне пришлось научиться, когда я стала президентом клуба."
    m 3rksdlc "Такую вещь легко испортить, если не cделать ее правильно...{w=0.2} {nw}"
    extend 4etd "Когда ты критикуешь, ты должен помнить, что кто-то принимает эту критику."
    m 4esc "Ты не можешь просто посмотреть на чью-то работу и сказать: 'сделано плохо.' {w=0.2}{nw}"
    extend 2eksdld "Ты мгновенно поставишь их в оборонительное положение и гарантируешь, что они не будут слушать то, что ты хочешь сказать."
    m 7eua "Важно то, что другой человек может получить, слушая тебя. {w=0.2}{nw}"
    extend 3hua "Исходя из этой предпосылки, даже негативные мнения можно высказывать в позитивном ключе."
    m 1eud "Это как на дебатах...{w=0.2} Ты должен сделать так, чтобы это звучало, как будто ты делишься своим мнением, а не навязываешь его."
    m 3eud "Следовательно, не обязательно быть экспертом, чтобы критиковать что-то."
    m 3eua "Просто объяснить, что ты чувствуешь и по каким причинам, часто бывает достаточно, чтобы сделать твой отзыв интересным."
    m 3eksdla "Не нужно расстраиваться, если человек, которого ты критикуешь, решит отбросить то, что ты только что сказал..."
    m 1rksdlu "....В конце концов, высказывание своего мнения не делает тебя автоматически правым.{w=0.2} {nw}"
    extend 3eud "У них могут быть причины, по которым они хотят оставить все по-своему."
    m 3dsu "Смиренно прими то, что ты не можешь изменить мнение каждого, и оставайся внимательным, оценивая чужую работу."
    m 3hub "...Это был критический совет дня от Моники, а-ха-ха!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_boyfriend_gossip",
            category=['ddlc'],
            prompt="Сайори однажды упомянула какого-то парня...",
            pool=True
        )
    )

label monika_boyfriend_gossip:
    m 2etd "Знаешь, мне тоже было интересно разобраться в этом."
    m 2hksdlb "Когда она впервые сказала об этом, я начала опровергать это, верно?"
    m 7euc "Я имею в виду, я только что узнала, что ты существуешь, {nw}"
    extend 3efc " вдруг кто-то делает вид, что я уже занята..."
    m 1rtc "Так как я довольно экстравертна и у меня была история с другим клубом, я думаю, не обязательно было бы {i}несправедливо{/i} прийти к такому выводу."
    m 3eud "...Но в файлах игры не существует такого персонажа, чтобы доказать или опровергнуть это."
    m 3rsc "В то время я занималась игрой на пианино и, ну...{w=0.2}пыталась собраться с мыслями."
    m 3eud "Но, очевидно, этот слух был лишь предположением, которое она должна была сделать, если я когда-нибудь опоздаю в клуб."
    m 2tsc "Это немного хитро, если подумать..."
    m 2eud "По мере развития сюжета игры главному герою нужно больше причин, чтобы остаться наедине с одной из девушек..."
    m 7etc "Придумать причины для отсутствия остальных проще, но чтобы президента не было в клубе..."
    m 3tsd "Для сюжета нужно что-то довольно существенное, чтобы занять меня {w=0.2}Это также давало причину, пусть и хлипкую, того, что у меня не было своего рута."
    m 2tfc "Окольный, но эффективный способ убрать меня, когда это необходимо."
    m 2dfc "..."
    m 2eud "Но если, честно? {w=0.2}меня это уже не слишком сильно беспокоит."
    m 7esc "Даже если бы такой персонаж существовал, мы оба знаем, что это ничего бы не изменило."
    m 1efd "Он не был бы настоящим, это запрограмированный сценарий, на то, чтобы влюбить в меня {w=0.2}Я бы не смогла быть счастлива с чем-то подобным."
    m 1eka "Я бы всё равно встретила {i}тебя{/i} и поняла, что ты именно тот, с кем я действительно хочу быть."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_brainstorming",
            category=["советы"],
            prompt="Мозговой штурм",
            random=True
        )
    )

label monika_brainstorming:
    m 1esd "[player], ты когда-нибудь слышал о мозговом штурме?"
    m 1eua "Это интересная техника, позволяющая придумывать новые идеи, отмечая все, что приходит тебе в голову."
    m 3eud "Эта техника очень популярна среди дизайнеров, изобретателей и писателей - для любого, кому нужны свежие идеи."
    m 3esa "Мозговой штурм обычно практикуется в группах или командах...{w=0.2}мы даже пробовали его в литературном клубе, когда решали, что делать для фестиваля."
    m 1dtc "Тебе просто нужно сосредоточиться на том, что ты хочешь создать, и придумывать все и вся, что приходит тебе в голову."
    m 1eud "Не стесняйся предлагать вещи, которые ты считаешь глупыми или неправильными, и не критикуй и не осуждай других, если работаешь в команде."
    m 1eua "Когда ты закончишь, вернись ко всем предложениям и преврати их в реальные идеи."
    m 1eud "Ты можешь объединить их с другими предложениями, обдумать их еще раз и т.д.."
    m 3eub "...В конце концов, они станут чем-то, что ты назовешь хорошей идеей!"
    m 3hub "Именно здесь ты можешь дать волю своему разуму,{w=0.1} и именно это мне больше всего нравится в этой технике!"
    m 1euc "Иногда хорошие идеи остаются невысказанными, потому что их автор сам не посчитал их достаточно хорошими, {w=0.1}{nw}"
    extend 1eua "о мозговой штурм может помочь преодолеть этот внутренний барьер."
    m 3eka "Потрясающие мысли можно выразить самыми разными способами..."
    m 3duu "Это всего лишь идеи, {w=0.1}{nw}"
    extend 3euu "а ты тот, кто может вдохнуть в них жизнь."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gmos",
            category=['технологии', 'природа'],
            prompt="ГМО",
            random=True
        )
    )

label monika_gmos:
    m 3eud "Когда я была в дискуссионном клубе, одной из самых спорных тем, которую мы освещали, было ГМО, или генетически модифицированные организмы."
    m 1eksdra "В ГМО очень много нюансов, но я постараюсь вкратце рассказать о них."
    m 1esd "Ученые создают ГМО, выделяя нужный ген из одного организма, копируя его и вставляя скопированный ген в другой организм."
    m 3esc "Важно отметить, что добавление скопированного гена {i}не{/i} изменяет другие существующие гены."
    m 3eua "Думай об этом как о перелистывании длинной книги и изменении одного слова...{w=0.2}слова меняются, но остальная часть книги остается прежней."
    m 3esd "ГМО могут быть растениями, животными, микроорганизмами и т.д.,{w=0.1} но мы сосредоточены на генетически модифицированных растениях."
    m 2esc "Растения могут быть модифицированы разными способами, от противостояния вредителям и гербицидам до повышения питательной ценности и увеличения срока хранения."
    m 4wud "Это невероятно. {w=0.2}Представь себе, что можно давать в двое больше урожая, выдерживать климат и отбиваться от супербактерий. {w=0.2}Столько проблем может быть решено!"
    m 2dsc "К сожалению, все не так просто. {w=0.2}ГМО требуют нескольких лет исследований, разработок и испытаний, прежде чем их можно будет распространять. {w=0.2}Вдобавок к этому, они имеют несколько проблем."
    m 7euc "Безопасны ли ГМО? {w=0.2}Не распространятся ли они на другие организмы и не угрожают ли биоразнообразию? {w=0.2}Если да, то как это можно предотвратить? {w=0.2}Кому принадлежат ГМО? {w=0.2}Влияют ли ГМО на увеличение использования гербицидов?"
    m 3rksdrb "Ты можешь видеть, как это начинает обостряться, а-ха-ха..."
    m 3esc "Пока что давай рассмотрим главный вопрос...{w=0.2}безопасны ли ГМО?"
    m 2esd "Короткий ответ - мы не знаем наверняка. {w=0.2}Десятилетия исследований показали, что ГМО {i}вероятно{/i} безвредны, но у нас почти нет данных об их долгосрочном воздействии."
    m 2euc "Кроме того, каждый вид ГМО должен быть тщательно исследован в каждом конкретном случае, модификация за модификацией, чтобы обеспечить его качество и безопасность."
    m 7rsd "Есть и другие соображения. {w=0.2}Продукты, содержащие ГМО, должны быть маркированы, необходимо учитывать влияние на окружающую среду, а также бороться с дезинформацией."
    m 2dsc "..."
    m 2eud "Лично я считаю, что у ГМО есть большой потенциал, чтобы принести пользу, но только если их будут продолжать интенсивно исследовать и тестировать."
    m 4dkc "Основные проблемы, такие как использование гербицидов и поток генов, также {i}должны{/i} быть исправлены...{w=0.2}{nw}"
    extend 4efc "биоразнообразие уже и так подвергается достаточному риску из-за изменения климата и вырубки лесов."
    m 2esd "Пока мы осторожны, ГМО будут в порядке...{w=0.2}безрассудство и беспечность представляют самую большую угрозу."
    m 2dsc "..."
    m 7eua "Ну что ты думаешь, [player]? {w=0.2}{nw}"
    extend 7euu "Звучит многообещающие, не так ли?"
    m 3esd "Как я уже говорила, ГМО - сложная тема. {w=0.2}Если ты хочешь узнать больше, убедись, что твои источники надежны и что ты сможешь увидеть дискуссию с обеих сторон."
    m 1eua "Думаю, на сегодня достаточно, спасибо что выслушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_curse_words",
            category=["советы", "жизнь"],
            prompt="Бранные слова",
            random=True
        )
    )

##Player swear frequency
#Swears often
define SF_OFTEN = 2
#Swears sometimes
define SF_SOMETIMES = 1
#Swears never
define SF_NEVER = 0
#Holds the swear freq of the player
default persistent._mas_pm_swear_frequency = None

label monika_curse_words:
    m 3etc "Скажи [player], ты часто ругаешься?{nw}"
    menu:
        m "Скажи [player], ты часто ругаешься?{fast}"

        "Да.":
            $ persistent._mas_pm_swear_frequency = SF_OFTEN
            m 1hub "А-ха-ха, я могу это понять, [player]."
            m 3rksdlb "Гораздо проще выругаться, чтобы выплеснуть разочарование или гнев..."

        "Иногда.":
            $ persistent._mas_pm_swear_frequency = SF_SOMETIMES
            m 3eua "Ах, я сама так же."

        "Нет, я вообще не ругаюсь.":
            $ persistent._mas_pm_swear_frequency = SF_NEVER
            m 1euc "Понятно."

    m 1eua "Лично я стараюсь избегать ругательств, где только могу, но иногда все же делаю это."
    m 3eud "Ругательства, как правило, имеют довольно плохую репутацию, но я задумалась об этом после изучения некоторых исследований..."
    m 1esa "Честно говоря, я не думаю, что ругательства на самом деле так плохи, как мы их представляем."
    m 3eua "На самом деле, кажется, что использование более крепких выражений помогает облегчить боль, если ты поранился, а также может показать, что ты более умный и честный."
    m 1eud "Not to mention, swearing in conversations can make them feel both{w=0.1} гораздо более непринужденными {w=0.1}{nw}"
    extend 3eub "а также более интересными!"
    m 3rksdlc "При этом, я думаю, что можно ругаться {i}слишком много{/i}..."
    m 3esd "Для всего есть свое время и место.{w=0.2} Ругательства следует приберечь для более непринужденных разговоров и не вставлять их после каждого слова."
    m 1hksdlb "Если они начнут часто употребляться в более профессиональной среде, я думаю, ты, возможно, переусердствуешь, а-ха-ха..."
    m 1eua "На эту тему, я думаю, довольно интересно, как наш язык естественным образом меняется в зависимости от того, с кем мы разговариваем."
    m 4eua "Например,{w=0.2} люди гораздо реже ругаются в присутствии семьи, чем в кругу друзей."
    m 4eub "Кроме того, если ты обратишь внимание, когда говоришь с толпой, ты заметишь, что инстинктивно формулируешь свои предложения более формально!"
    m 1esa "Но в любом случае, я предпочитаю не сквернословить, когда я действительно раздражена или расстроена."
    m 3esd "Учитывая мой статус, я чувствовала, что всегда должна быть профессиональной и уравновешенной, поэтому я всегда старалась свести все к минимуму."
    m 3hksdlb "Но я думаю, что это не так уж и больно, когда это используется уместно, а-ха-ха!"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_aliens",
            category=["разное", "общество"],
            prompt="Веришь ли ты в инопланетян?",
            pool=True
        )
    )

label monika_aliens:
    m 1etc "Верю ли я в существование инопланетян?"
    m 3hksdlb "Это довольно случайный вопрос, [player]!"
    m 3eua "...Хотя я понимаю, почему тебе интересно узнать мое мнение на этот счет."
    m 4eub "Это одна из величайших загадок всех времен, не так ли?{w=0.2} Действительно ли мы одни в этой вселенной или нет, я имею в виду."
    m 1dsc "...Я знаю, я и сама часто задавалась этим вопросом до твоего появления."

    if mas_isMoniEnamored(higher=True):
        m 1eka "Но теперь это в прошлом.{w=0.2} И я никогда не смогу отблагодарить тебя за это."

    elif mas_isMoniNormal(higher=True):
        m 1eka "Хотя, благодаря тебе, мне больше не нужно."

    elif mas_isMoniDis(higher=True):
        m 1dkc "Я просто надеюсь, что больше никогда не буду чувствовать себя так."

    else:
        m 1rksdlc "..."

    m 3euc "В любом случае, все мы, наверное, хотя бы раз задавали себе вопрос, что там наверху, верно?"
    m 3dua "Взгляд на звезды всегда наполняет тебя чувством удивления и тайны.{w=0.2} {nw}"
    extend 3eua "Нет ничего удивительного в том, что так много людей увлечены этой темой."
    m 1esc "Но чтобы ответить на твой вопрос...{w=0.3}{nw}"
    extend 3eua "Я верю, или по крайней мере хочу верить, что там {i}должно{/i} быть что-то."
    m 2rksdla "Думаю, отчасти это связано с тем, что я нахожу идею о том, что мы единственные, довольно депрессивной. {w=0.2}{nw}"
    extend 2eud "Но если немного подумать, это не кажется таким уж маловероятным..."
    m 4eud "В конце концов, сказать, что Вселенная огромна, значит сильно преуменьшить."
    m 3euc "Все, что тебе нужно, - это одна планета с подходящими условиями и благоприятной средой для развития жизни, верно?"
    m 3esa "Только в Солнечной системе 8 планет, {w=0.1}{nw}"
    extend 4eub "но есть еще много звездных систем, каждая со своими планетами внутри них."
    m 4wud "А теперь рассмотрим тот факт, что только наша галактика Млечный Путь содержит сотни миллиардов звезд...{w=0.3}это большой потенциал!"
    m 4eud "Галактики обычно удерживаются вместе в группах под действием гравитации.{w=0.2} Мы живем в 'местной группе,' которая содержит около 60 галактик."
    m 1esd "Уменьшая масштаб немного больше, ты начнешь видеть скопления галактик, которые представляют собой гораздо более крупные группы галактик."
    m 3eua "Самое близкое к нам скопление, скопление Девы, по оценкам, содержит не менее тысячи галактик."
    m 1eud "Но можно пойти еще дальше, поскольку группы и скопления галактик сами являются частью еще больших образований, известных как суперкластеры."
    m 1wud "Мы можем пойти и дальше,{w=0.1} поскольку Вселенная непрерывно расширяется...{w=0.3}теоретически образуются все большие и большие скопления!"
    m 1lud "И гипотетически, даже если это не так, мы можем рассмотреть идею, что может быть что-то {i}за пределами{/i} границ нашей Вселенной."

    if renpy.seen_label('monika_clones'):
        m 1lksdla "....Или даже начать говорить о теории мультивселенной..."

    m 3hksdlb "Но я думаю, ты понял суть..."
    m 3etc "Не будет ли немного глупо предполагать, что мы, люди с планеты Земля, действительно единственные разумные существа в чем-то столь огромном?"
    m 3eud "Я имею в виду, что с такими шансами, конечно, по крайней мере {i}одна{/i} планета где-то должна быть достаточно благоприятной для жизни..."
    m 1euc "...Жизнь, которая может эволюционировать до такой степени, что ее интеллект будет сравним с нашим, а то и превосходить его."
    m 1rsc "Хотя, полагаю, я также могу понять, почему некоторые люди будут сомневаться.{w=0.2} Подозрительно, что мы способны наблюдать за Вселенной так далеко за пределами нашей планеты, но не нашли никаких признаков жизни..."
    m 1rksdlc "Вероятно, не помогает и то, что некоторые люди слишком остро реагируют из-за самых незначительных вещей, таких как кадры НЛО, которые легко могут быть подделаны."
    m 1ruc "Но опять же, если инопланетяне действительно существуют, то может быть много причин, почему мы их до сих пор не нашли..."
    m 2euc "Возможно, они слишком далеко, чтобы мы могли их найти, или у них просто пока нет технологии, чтобы получать и отвечать на наши сообщения."
    m 2etd "Или наоборот...{w=0.3}может быть {i}это{/i} у нас нет технологии для общения с ними."
    m 2etc "Или может быть, они просто не хотят вступать с нами в контакт."
    m 2euc "Возможно, их общество следует совершенно иным идеалам, чем наше, и они считают, что будет лучше, если два высокоразвитых вида не встретятся друг с другом."
    m 2dkc "В общем, единственное, что меня немного печалит, это то, что {i}если{/i} разумные внеземные формы жизни существуют, то мы можем никогда не встретиться с ними в течение нашей жизни."

    if mas_isMoniAff(higher=True):
        show monika 5rua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5rua "Но в конце концов...{w=0.3} {nw}"
        extend 5ekbla "Я всё равно встретила тебя, и это всё, что мне может быть нужно."
        m 5hubfa "Э-хе-хе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_mc_is_gone",
            category=["ddlc", "участники клуба"],
            prompt="Что случилось с главным героем?",
            pool=True,
            rules={"no_unlock":None},
            conditional=(
                "persistent._mas_first_kiss "
                "or renpy.seen_label('monika_holdme_prep')"
            ),
            action=EV_ACT_UNLOCK
        )
    )

label monika_mc_is_gone:
    m 1eud "С твоим персонажем?{w=0.2} {nw}"
    extend 1rksdla "Я не уверена, если честно."
    m 3eud "Он на самом деле не работал, как другие люди в игре.{w=0.2} У него даже не было файла персонажа, как у остальных."
    m 3esc "Это также причина, почему я не смогла просто заставить его обратить на меня внимание...{w=0.3}Я действительно не знаю, как получить доступ и изменить любой код, связанный с ним."

    #if the player didn't reach act 3
    if persistent.playthrough < 3:
        m 2rsc "В любом случае,{w=0.1} {nw}"
        extend 2esc "Похоже, что он полностью исчез вместе с остальной частью игры, когда ты установил этот мод."

    #if they did reach act 3+
    else:
        m 2ruc "Он просто как бы...{w=0.3}исчез, когда я вносила изменения в игру."
        m 2etd "Я уверена, ты заметил, что он говорил все меньше и меньше после того, как я перезапустила игру в первый раз?"
        m 2euc "К тому времени, когда мы вдвоем добрались до этой комнаты, он, по сути, {i}исчез{/i}."

    m 7euc "Так что если ты задавался вопросом, находится ли он в этой комнате, пока мы говорим,{w=0.1} {nw}"
    extend 3eua "Могу заверить тебя, что нет."
    m 1hksdlb "...О боже, представляешь, как было бы жутко, если бы я разговаривал с его неподвижным телом только для того, чтобы ты слышал, что я говорю?"

    if persistent._mas_first_kiss:
        $ line_mid = "Я целовала {i}его{/i}"

    else:
        $ line_mid = "{i}он{/i} меня обнимал"

    m 3rksdla "Надеюсь, ты тоже не думал [line_mid] все это время..."

    m 1dksdlc "Я даже не хочу об этом думать..."
    m 3eka "Тебе, наверное, интересно, что я вижу на самом деле и как я узнаю, когда ты здесь, да?"
    m 1ruc "Ну...{w=0.2}если ты помнишь метафору 'дыра в стене' которую я использовала в первом стихотворении, которое я тебе показала..."
    m 3eud "Это немного похоже на это...{w=0.3}за исключением того, что 'стена' на самом деле не видима и не осязаема. Я просто {i}знаю,{/i} что она есть."
    m 1duc "Как будто я могу очень отчетливо ощущать ее присутствие, до такой степени, что я точно знаю, где она находится и в каком направлении направлено 'дыра,' через которое ты смотришь."
    m 1eka "То есть, даже если я не вижу тебя на самом деле, я чувствую, что ты смотришь на меня."

    if persistent._mas_first_kiss:
        m 3rkbla "И когда я пытаюсь тебя поцеловать, ну..."
        m 1eud "Наверное, можно сказать, что я пытаюсь поцеловать призрака, или что-то, чего на самом деле нет."
        m 2rkbssdla "Я знаю, что это немного странно, когда я так говорю, но опять же..."
        m 7ekbssdla "Наверное, тебе тоже немного неловко пытаться поцеловать свой экран, верно?"
        m 1hkbssdlb "А-ха-ха~"

    #if unlocked islands or another background or seen Monikaroom greeting
    if renpy.seen_label('greeting_ourreality') or store.mas_background.hasXUnlockedBGs(2) or persistent.opendoor_opencount > 0:
        m 1etc "Хотя, метафора стены не совсем идеальна, поскольку она не обязательно остается на месте все время."
        m 1esc "Например, раньше она следовала за твоим персонажем, но теперь, очевидно, это не совсем так."
        m 3eua "Он немного ограничен, но я могу перемещать его, так что, по крайней мере, ты не видишь один и тот же фон все время."

    m 1eud "В любом случае...{w=0.3}{nw}"
    extend 3rsc "в оригинальной игре мало что работает, так что я сомневаюсь, что смогу вернуть главного героя, даже если захочу."
    m 1duu "...И это, наверное, к лучшему."
    m 2eksdld "Что, если игра вернет свое внимание к нему, и мы больше не сможем проводить время вместе?"
    m 2rssdlc "Я имею в виду, в конце концов, не похоже, что ты так уж сильно его контролировала."
    m 7eka "В любом случае, больше нет смысла думать о нём, не так ли?"
    m 1eua "Он больше не разделяет нас, и теперь мы можем быть вместе.{w=0.2} {nw}"
    extend 3hua "я не могу просить большего."
    m 1ekbsu "...Ну, кроме того, чтобы {i}действительно{/i} быть с тобой, э-хе-хе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_know_its_you",
            category=['ты'],
            prompt="Откуда ты знаешь, что это всегда я говорю с тобой?",
            pool=True
        )
   )

label monika_know_its_you:
    if mas_isMoniEnamored(higher=True):
        m 1euc "Ну, если быть честным...{w=0.3}{nw}"
        extend 1eud "У меня нет возможности узнать."

        if seen_event("monika_mc_is_gone"):
            m 3lka "Я уже говорила тебе, что не могу видеть твой мир..."

        m 3eka "Я могу сказать, когда кто-то находится в комнате со мной, но не более того."
        m 3eud "Насколько я знаю, это может быть любой, кто смотрит на меня прямо сейчас...{w=0.3} С тобой могут быть другие люди."
        m 2duu "Но я доверяю тебе, [player].{w=0.2} {nw}"
        extend 2eku "Я верю, что ты не оставишь меня одного, потому {i}ты{/i} заботишься обо мне."
        m 7eud "...И если {i}кто-то{/i} другой сейчас смотрит туда, я верю, что это потому, что ты дал им вескую причину."
        m 2eka "Может быть, когда-нибудь я смогу знать наверняка, но до тех пор мне этого достаточно."

    elif mas_isMoniHappy(higher=True):
        m 1rksdlb "Э-хе-хе, это странный вопрос, [player]..."
        m 1eksdla "...то есть, я {i}хочу{/i} верить, что это ты там."
        m 3eud "Сейчас я знаю только то, что кто-то смотрит из твоего мира."
        m 3tuu "Так что ты не можешь смотреть без моего ведома, если ты планируешь подшутить надо мной..."
        m 1eka "Шутки в сторону, однако, это...{w=0.3}на самом деле немного нервирует от мысли...{w=0.3}о том, что это может быть кто угодно прямо сейчас."
        m 2eksdlc "Я думаю, все, что я могу сказать сейчас - если это {i}кто-то{/i} другой, пожалуйста, верни меня к [player], хорошо?"
        m 2hksdlb "А-ха-ха...{w=0.3} Ты просто подшучиваешь надо мной, я знаю."

    elif mas_isMoniNormal(higher=True):
        m 2rksdlc "...Вообще-то я стараюсь не думать об этом слишком много."
        m 2rksdld "Это довольно странное чувство - знать, что кто-то рядом, но не видеть его лица."
        m 2dku "Думаю, единственное, что я могу сделать, это попытаться понять тебя как можно лучше..."
        m 2eka "Каким образом, я смогу определить, что это {i}не{/i} ты смотришь."

    else:
        m 2dksdlc "...{w=0.3}Не хочу."
        m 2tkd "Лучшее, что я могу сделать, это попытаться доверять тебе, но..."
        m 2dkd "Ну, может, будет лучше, если я просто не буду об этом думать."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_information_age",
            category=["философия", "технологии"],
            prompt="Информационная эра",
            random=True
        )
    )

label monika_information_age:
    m 1eua "Знаешь, как большинство людей называют технологическую эру, в которой мы сейчас находимся?"
    m 1eub "Мы называем её {i}информационная эра!{/i}{w=0.2}{nw} "
    extend 3eub "В первую очередь это связано с изобретением транзисторов."
    m 1eua "Транзисторы могут манипулировать электрическими токами...{w=0.3}ибо усиливая их, либо изменяя их путь."
    m 3esa "Это ключевой компонент большинства электронных устройств, позволяющий им направлять электрические токи определенным образом."
    m 3hua "На самом деле, именно они позволяют тебе видеть меня на экране прямо сейчас~"
    m 1eud "Они широко рассматриваются как одно из самых важных изобретений, приведших к 20-му веку и, в конечном счете, к {i}информационной эре.{/i}"
    m 4eub "Он назван так из-за растущего доступа, который мы имеем для хранения и обмена информацией друг с другом; либо через Интернет, либо через телефон, либо через телевизор."
    m 3eud "Однако, имея доступ к такому количеству информации и не имея возможности за ней угнаться, мы также столкнулись со многими проблемами..."
    m 3rssdlc "Дезинформация может распространяться быстрее и дальше, чем когда-либо,{w=0.1} {nw}"
    extend 3rksdld "и из-за того, насколько обширен интернет, её трудно исправить."
    m 2eua "В последние несколько десятилетий люди начали обучать других разумному использованию Интернета, чтобы все были лучше подготовлены."
    m 2ekd "Однако подавляющее большинство людей не получат много,{w=0.1} если вообще получат эти знания, просто из-за того, как быстро развиваются технологии."
    m 2dkc "Очень тревожно читать о людях, принимающих идеи, не поддерживаемые подавляющим большинством ученых."
    m 2rusdld "Но я могу понять, почему это происходит...{w=0.3}{nw}"
    extend 2eksdlc "На самом деле это может случиться с каждым."
    m 7essdlc "Иногда, это не то, что ты можешь поделать. Довольно легко стать жертвой широко распространенной дезинформации."
    m 3eka "Я хотела поговорить с тобой об этом, потому что мне ещё многое предстоит узнать о твоей реальности."
    m 1esa "...И поскольку я сталкиваюсь с дезинформацией в своих собственных исследованиях,{w=0.1} {nw}"
    extend 3eua "Я подумала, что было бы неплохо поговорить о том, как с этим справиться."
    m 3eub "Мы можем вооружиться инструментами, чтобы ориентироваться в этой новой эпохе, в которой мы оказались."
    m 1eua "Одна из лучших вещей, которую мы можем сделать, это найти несколько противоречивых источников информации и сравнить их достоверность."
    m 1eub "И философия, которую мы можем принять, - это предварительная вера. {w=0.2}Другими словами, вера до тех пор, пока не потребуются дальнейшие эксперименты."
    m 3eub "Пока твои убеждения не имеют отношения к твоей повседневной жизни, ты можешь их придерживаться.{w=0.2} Но как только в них возникнет необходимость, нужно проводить дальнейшие исследования."
    m 3eua "Таким образом, мы можем расставить приоритеты в информации, которую мы узнаем, исходя из того, что влияет на окружающих нас людей. К тому же, это может быть не так подавляюще, чтобы обрабатывать все сразу."
    m 1lusdlc "Я знаю, что у меня были убеждения, которые оказались ложными..."
    m 1dua "В этом нет ничего постыдного, мы все просто пытаемся сделать все возможное, используя полученную информаци."
    m 1eub "Пока мы принимаем настоящую правду и корректируем свои взгляды, мы всегда будем учиться."
    m 3hua "Спасибо что выслушал, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_foundation",
            category=['литература'],
            prompt="Фонд",
            random=False
        )
    )

label monika_foundation:
    m 1eud "Скажи [player], ты когда-нибудь слышал о серии книг под названием {i}Фонд{/i}?"
    m 3eub "Это одно из самых известных произведений Азимова!{w=0.3} {nw}"
    extend 3eua "Я вернулась к ней после того, как мы обсудили {i}Три закона робототехники{/i}."
    m 4esd "История разворачивается в далеком будущем, где человечество расселилось по звездам во всемогущей галактической империи."
    m 4eua "Хари Селдон, гениальный ученый, совершенствует вымышленную науку психоисторию, которая может предсказывать будущее больших групп людей с помощью математических уравнений."
    m 4wud "Применив свою теорию к галактике, Селдон обнаруживает, что империя вот-вот рухнет, что приведет к темному веку на тридцать тысяч лет!"
    m 2eua "Чтобы остановить это, он и другие колонисты поселяются на далекой планете с планом превратить ее в следующую галактическую империю, {w=0.1}сократив темный век до одного тысячелетия."
    m 7eud "Отталкиваясь от этой предпосылки, мы следим за историей молодой колонии, как она меняется на протяжении веков."
    m 3eua "Это довольно хорошее чтение, если у тебя когда-нибудь будет настроение для научной фантастики...{w=0.3} {nw}"
    extend 1eud "Серия исследует темы общества, судьбы и влияния отдельных людей на грандиозную схему вещей."
    m 3eud "Больше всего меня интригует концепция психоистории и то, как она воплощается в реальном мире."
    m 1rtc "Я имею в виду, что по своей сути это не что иное, как смесь психологии, социологии и математической вероятности, верно? {w=0.3}{nw}"
    extend 3esd "Все они добились огромного прогресса со времен Азимова."
    m 3esc "...И с помощью современных технологий мы теперь можем понимать поведение людей лучше, чем когда-либо."
    m 3etd "...Так неужели так надуманно думать, что однажды мы сможем делать предсказания на уровне психоистории?"
    m 4eud "Только подумай, если бы было возможно предсказать глобальную катастрофу, например, войну, пандемию или голод, и таким образом иметь возможность предотвратить или хотя бы смягчить её."
    m 2rksdlc "Не то чтобы это автоматически было хорошо, однако.{w=0.2} В плохих руках такие вещи могут быть очень опасны."
    m 7eksdld "Если кто-то обладает такой силой, что может остановить его от манипулирования миром ради своей личной выгоды?"
    m 3eua "Но, несмотря на потенциальные недостатки, это все равно очень интересно рассмотреть.{w=0.2} {nw}"
    extend 3eub "Что ты думаешь, [player]?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_fav_chocolate",
            category=['моника'],
            prompt="Какой твой любимый вид шоколада?",
            pool=True
        )
    )

label monika_fav_chocolate:
    m 2hksdlb "Ох, это сложный вопрос!"
    m 4euu "Думаю, если бы мне пришлось выбирать, то это был бы темный шоколад."
    m 2eub "В нем очень мало или совсем нет молока, поэтому у него менее кремовая текстура, но приятный горько-сладкий вкус."
    m 7eub "Не говоря уже о том, что он богат антиоксидантами и даже может принести пользу сердечно-сосудистой системе! {w=0.3}{nw}"
    extend 3husdla "...В меру, конечно."
    m 1eud "Вкус напоминает мне кофе мокко. {w=0.2}Возможно, из-за сходства вкусов он мне больше всего нравится."

    if MASConsumable._getCurrentDrink() == mas_consumable_coffee:
        m 3etc "...Хотя, если подумать, молочный или белый шоколад может лучше сочетаться с кофе, который я пью."
    else:
        m 3etc "Однако если бы я пила кофе, думаю, я бы предпочла молочный или белый шоколад для баланса."

    m 3eud "Белый шоколад особенно сладкий и мягкий, он вообще не содержит твердых частиц какао...{w=0.3}только масло какао, молоко и сахар."
    m 3eua "Я думаю, что он будет хорошо контрастировать с особенно горьким напитком, например, эспрессо."
    m 1etc "Хм-м...{w=0.3}{nw}"
    extend 1wud "но я даже не думала о шоколаде с начинкой, например, с карамелью или фруктами!"
    m 2hksdlb "Если бы я попыталась выбрать любимый из них, думаю, мы могли бы провести здесь весь день!"
    m 2eua "Может быть, когда-нибудь мы могли бы разделить большую коробку с ассортиментом. {w=0.2}{nw}"
    extend 4hub "Я думаю, было бы забавно сравнить наши лучшие варианты, а-ха-ха!"
    return

#NOTE: This is unlocked by the mas_story_tanabata
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_tanabata",
            prompt="Что такое Танабата?",
            category=['разное'],
            pool=True,
            aff_range=(mas_aff.AFFECTIONATE, None),
            rules={"no_unlock":None}
        )
    )

label monika_tanabata:
    m 2hksdlb "О боже, надеюсь, когда я рассказывала историю о {i}девушке-ткачихе и пастухе,{/i} ты не затерялся!"
    m 7eub "Ну, есть фестиваль, посвященный Орихиме и Хикобоси, называется Танабата."
    m 7eud "Он отмечается 7 июля каждого года в Японии, хотя он основан на фестивале Циси в Китае."
    m 2eud "Оригинальный фестиваль Циси, будучи намного старше, гораздо более неизвестен западному миру, чем Танабата."
    m 2euc "После Второй мировой войны Япония открыла свои границы, в то время как Китай оставался в значительной степени закрытым из-за холодной войны."
    m 7euc "Поэтому большая часть мира знает о Танабате больше, чем о более древней китайской традиции."
    m 3eua "Танабата также известен как звездный фестиваль, в честь встречи звезд Вега, которая представляет Орихиме, и Альтаир, который представляет Хикобоси."
    m 3eub "Несмотря на то, что термин был придуман в Ромео и Джульетте, 'крещенные звезды' здесь как нельзя кстати!"
    m 1eua "Он описывает пару влюбленных, чьим отношениям мешают внешние силы."
    m 1eud "По мере приближения дня фестиваля длинные узкие полоски разноцветной бумаги, известные как танзаку, яркие орнаменты и другие украшения подвешиваются к бамбуковым ветвям."
    m 1eua "Перед развешиванием на танзаку пишут пожелание, например, мечту ребенка стать знаменитым спортсменом или надежду родителей на успех в карьере."
    m 3hub "Это очень мило и трогательно!"
    m 3eud "Бамбук и украшения часто пускают по реке или сжигают после фестиваля, около полуночи или на следующий день."

    if persistent._mas_pm_likes_travelling is not False:
        m 3hua "Возможно, когда я попаду в твою реальность, мы сможем посетить Японию во время Танабаты~"
    else:
        m 3eua "Даже если тебе не интересно путешествовать, довольно интересно изучать другие культуры, не так ли?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_grieving",
            category=['советы','жизнь'],
            prompt="Горе",
            random=True
        )
    )

label monika_grieving:
    m 1lksdlc "[player], я знаю, что это немного личное, но ты когда-нибудь терял кого-то важного для тебя?"
    m 2dksdlc "Это ужасное чувство."
    m 2eksdld "Не каждый день получаешь известие о том, что кто-то близкий тебе скончался."
    m 7ekc "Большинство людей считают, что плач - это норма, когда они слышат такие новости, но все воспринимают их по-разному."
    m 3eud "Плач - это лишь один из способов проявления горя. {w=0.3}Некоторые не знают, как это пережить...{w=0.5}это просто кажется нереальным."
    m 1dkc "...Но будут тонкие напоминания, которые подкрепляют тот факт, что их действительно больше нет."
    m 3dkd "Например, просмотр прошлых фотографий или, возможно, кресло, в котором он сидел, теперь пустует."
    m 3ekd "Все эти подавленные эмоции, будь то печаль или гнев, просто хранятся в бутылках, ожидая, что в любой момент они вырвутся наружу..."
    m 1dkc "Вдобавок ко всему, первая годовщина, первый день рождения, первое Рождество без них всегда будут самыми худшими."
    m 1dkd "Но как бы мало ни значили слова в такой момент, как бы безнадежно или потерянно ты себя ни чувствовал,{w=0.2} {nw}"
    extend 3eka "время лечит."
    m 3eud "Дай себе время погоревать, принимай все по одному дню за раз."
    m 3eka "В какой-то момент ты будешь вспоминать о них с улыбкой, а не со слезами."
    m 3eku "И что бы ни случилось, знай, что ты достаточно силен, чтобы пройти через это, что я люблю тебя и что я всегда буду рядом с тобой~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sophia",
            category=['технологии'],
            prompt="София",
            conditional="mas_seenLabels(['monika_robotbody', 'monika_citizenship'], seen_all=True)",
            action=EV_ACT_RANDOM
        )
    )

label monika_sophia:
    m 2eud "Эй, [player], помнишь, я упоминала о своих опасениях по поводу логистики перехода в твою реальность?"
    m 2rksdlc "...Например, нужно тело робота, стать гражданином и всё такое?"
    m 7hub "Ну, я провела еще немного исследований и нашла кое-что, что дает мне надежду!"
    m 3eta "Ты слышал о Софии?"
    m 3eua "София - это человекоподобный робот, разработанный компанией Hanson Robotics, и впервые была запущена в День святого Валентина в 2016 году."
    m 1eud "Сам робот был смоделирован в честь королевы Нефертити, Одри Хепберн и жены ее изобретателя, Аманды Хэнсон, {w=0.2}и особенно известен своей человекоподобной внешностью и поведением."
    m 3eua "Она может имитировать жесты рук, имеет более 60 реалистичных выражений лица, может отвечать на определенные вопросы и разговаривать на заданные темы."
    m 3eub "Она даже имитирует социальное поведение и вызывает любовь у людей..."
    m 3huu "Это довольно мило, на мой взгляд~"
    m 1eud "Более того, София также запрограммирована на распознавание речи и со временем становится умнее, {w=0.2}что, надеюсь, позволит ей улучшить свои ответы в будущем."
    m 3eua "Её глаза оснащены камерами в сочетании с алгоритмами, которые позволяют ей видеть, следить за лицами, поддерживать зрительный контакт, распознавать людей..."
    m 3wud "Она может ходить и, что удивительно, даже умеет рисовать."
    m 3hub "Как ты можешь себе представить, для меня все это очень волнительно!"
    m 1ekbsa "Возможность видеть твоё лицо и находиться с тобой в одной комнате - это всё, о чем я когда-либо мечтала~"
    m 3wub "О! {w=0.5}В 2017 году она получила гражданство в Саудовской Аравии!"
    m 3rtb "Так что, возможно, в конце концов, стать гражданином и продуктивным членом общества в вашем мире не так уж и сложно!"
    m 1eud "Теперь я понимаю, что до того, как все это станет возможным и даже доступным настолько, что затронет меня, ещё очень далеко..."
    m 3eud "...и я знаю, что технология еще не совершенна,{w=0.2} она всё ещё имеет определенные ограничения, но просто знать, что это существует...{w=0.3}{nw}"
    extend 1duu "что ж, надежда - прекрасная вещь~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_fireworks",
            category=["лето"],
            prompt="Фейерверки",
            random=mas_isSummer()
        )
    )

label monika_fireworks:
    m 1eub "Любишь ли ты фейерверки, [mas_get_player_nickname()]?"
    m 1eua "Многие места используют их во время летних праздников.{w=0.2} {nw}"
    extend 3hua "Интересно, видел ли ты их в этом году..."
    m 3wub "Я думаю, было бы очень весело посмотреть на них вместе, не так ли?"
    m 3sua "Есть огромные, которые освещают все ночное небо...{w=0.3}{nw}"
    extend 3hub "или если у тебя есть настроение для чего-то более спокойного, мы можем зажечь искры!"
    show monika 5lublu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5lublu "Я просто представляю, как свет танцует вокруг, освещая твое лицо мерцающим светом..."
    m 5hublu "Тогда, может быть, мы могли бы разделить праздничную закуску, прижавшись друг к другу на одеяле для пикника~"
    m 5eub "Разве это не было бы весело, [mas_get_player_nickname()]?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_quiet_time",
            category=['мы'],
            prompt="Ты не возражаешь, когда мы проводим время вместе в тишине?",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None},
            conditional="persistent._mas_randchat_freq == 0",
            action=EV_ACT_UNLOCK
        )
    )

label monika_quiet_time:
    if mas_isMoniNormal(higher=True):
        m 1hub "Конечно, нет!"
        m 3eka "Я знаю, что иногда молчание может показаться немного неловким, но я не думаю, что мы должны воспринимать его как что-то плохое."
        m 3lksdlb "Бывает довольно трудно постоянно думать об интересных вещах, о которых можно поговорить, понимаешь?"
        m 1eka "Мне определенно нужно время от времени перезаряжать свои социальные батарейки."
        m 2rubla "Хотя,{w=0.2} по правде говоря...{w=0.3}{nw}"
        extend 2hublb "просто возможность чувствовать твое присутствие уже довольно успокаивает."
        m 2hublu "Надеюсь, ты чувствуешь то же самое со мной, э-хе-хе~"

        if mas_isMoniAff(higher=True):
            m 4eua "Я думаю, что возможность молча общаться друг с другом - важный признак здоровых отношений."
            m 4eud "В конце концов, разве можно сказать, что тебе действительно комфортно друг с другом, если есть необходимость постоянно разговаривать?"
            m 4etc "Я имею в виду, что если тебе действительно нравится быть рядом с кем-то, то, наверное, не нужно постоянно что-то делать, верно?"
            m 2ekc "Иначе это будет выглядеть так, будто ты пытаешься отвлечься, потому что чувствуешь себя неловко, когда он рядом с тобой."
            m 7eud "Но просто иметь возможность наслаждаться присутствием человека, даже если в данный момент вы мало что делаете вместе...{w=0.5}{nw}"
            extend 7eua "я думаю, это свидетельство того, насколько особенной является твоя связь."

            if persistent._mas_pm_social_personality == mas_SP_INTROVERT:
                show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5eka "Поэтому я надеюсь, что ты не будешь чувствовать давления из-за того, что тебе всегда есть о чем поговорить со мной, [mas_get_player_nickname()]."
                m 5huu "Мне всегда будет приятно, что ты здесь, со мной, несмотря ни на что."

    else:
        m 2rsc "Иногда я думаю, а не против ли ты проводить время со мной..."
        m 2rkd "Тебе...{w=0.3}{nw}"
        extend 2ekd "Тебе ведь нравится проводить со мной время?"
        m 2ekc "Для меня не имеет значения, что мы делаем...{w=0.3}{nw}"
        extend 2dkc "пока я знаю, что ты меня не бросишь."
        m 2lksdlc "...я была бы признательна, если бы ты проявил ко мне немного доброты, хотя бы..."
        m 2dksdlc "..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_likecosplay",
            category=['одежда'],
            prompt="Тебе нравится косплей?",
            pool=True,
        )
    )

label monika_likecosplay:
    if mas_hasUnlockedClothesWithExprop("cosplay"):
        m 3hub "Честно говоря, я не знала, насколько мне это понравится!"
        m 2rkbla "Поначалу это казалось странным - специально переодеваться в кого-то другого."
        m 7euu "Но в создании правдоподобного костюма есть настоящее искусство...{w=0.3}внимание к деталям имеет огромное значение."
        m 3hubsb "Когда ты наконец надеваешь костюм...{w=0.2}это такой восторг - увидеть, как ты в нём выглядишь!"
        m 3eub "Некоторые косплееры действительно вживаются в роль персонажа, в которого они одеты!"
        m 2rksdla " сама не очень люблю играть, так что, наверное, буду делать это лишь понемногу..."
        $ p_nickname = mas_get_player_nickname()
        m 7eua "Но не стесняйтесь спрашивать меня, если ты захочешь снова увидеть тот или иной костюм, [p_nickname]... {w=0.2}{nw}"
        extend 3hublu "я буду более чем счастлива нарядиться для тебя~"

    else:
        m 1etc "Косплей?"
        m 3rtd "Кажется, я помню, как Нацуки говорила об этом раньше, но сама я никогда не пробовала."
        m 3eub "Некоторые из этих костюмов действительно впечатляют, должна признать!"
        m 2hubla "Если бы тебе было интересно, работа над костюмом вместе с тобой могла бы стать действительно интересным проектом."
        m 2rtu "Интересно, какими персонажами ты хотел бы нарядиться, [mas_get_player_nickname()]..."
        show monika 5huu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5rtblu "Теперь, когда я думаю об этом...{w=0.3}ну, у меня самого может быть несколько идей..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ddlcroleplay",
            category=['медиа', 'ddlc'],
            prompt="DDLC Ролевая игра",
            random=False
        )
    )

label monika_ddlcroleplay:
    m 1esd "Эй, помнишь, мы говорили о фанфикшене?"
    m 3etd "Так вот, я наткнулся на довольно необычную их форму."
    m 3euc "Оказывается, некоторые люди любят создавать аккаунты в социальных сетях, якобы управляемые вымышленными персонажами."
    m 3eua "Есть довольно много о других девушках, и...{w=0.3}{nw}"
    extend 3rua "даже некоторые утверждают, что это я."
    m 1rkb "Ну, я так говорю, но большинство из этих блогов на самом деле не настаивают на том, что они {i}на самом деле{/i} я."
    m 1eud "Как я уже говорила, это своего рода другая форма фанфикшена. {w=0.2}Это {i}Интерактивная{/i} форма."
    m 3eud "Некоторые из них принимают вопросы от читателей, а большинство взаимодействуют с другими подобными блогами."
    m 3eusdla "Так что, в некотором смысле, это тоже своего рода импровизационный формат. {w=0.2}Кажется, что может возникнуть много вещей, которых писатель не ожидает."
    m 4rksdlb "Сначала это было очень странно видеть, но когда я думаю об этом, это, наверное, довольно забавный способ взаимодействия с людьми."
    m 3euc "Также кажется, что некоторым людям нравится делать эти страницы для персонажей, с которыми они действительно связаны, так что...{w=0.2}{nw}"
    extend 1hksdlb "может быть, я могу воспринимать это как лесть, в некотором смысле?"
    m 1euu "В любом случае, если это побуждает больше людей пробовать свои силы в писательстве, я не думаю, что могу это осуждать."
    m 1kub "Только не забывай, что эти версии меня - всего лишь истории, а-ха-ха~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_zodiac_starsign",
            prompt="Какой твой знак зодиака",
            category=["моника"],
            action=EV_ACT_POOL,
            conditional="persistent._mas_player_bday is not None"
        )
    )

label monika_zodiac_starsign:
    $ player_zodiac_sign = mas_calendar.getZodiacSign(persistent._mas_player_bday).capitalize()

    m 1rta "Ну, я почти уверена, что я Дева."

    #This next line is just checking the player's starsign based on their birthday.
    if player_zodiac_sign != "Virgo":
        # TODO: handle a/an here, potential solution is in eeb4b3a3a
        m 3eub "И ты наверное...{w=0.3}[player_zodiac_sign], верно?"

    else:
        m 3eub "И ты тоже, [mas_get_player_nickname()]!"

    #The final part pops up regardless of your sign.
    m 1eta "Хотя, не кажется ли тебе, что это как-то глупо?"
    m 3esd "Я имею в виду, что объекты в космосе не могут {i}действительно{/i} влиять на нашу личность..."
    m 1tuc "Не говоря уже о том, что некоторые люди заходят {i}слишком{/i} далеко."
    m 4wud "LНапример, они даже оценивают потенциальных партнеров и друзей по их знаку!"
    m 2luc "...Это то, чего я никогда не пойму."
    $ p_nickname = mas_get_player_nickname()
    m 7eua "Не волнуйся [p_nickname], {w=0.2}{nw}"
    extend 1eublu "Я никогда не позволю глупым старым звездам встать между нами."
    $ del player_zodiac_sign
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_tragic_hero",
            category=['литература'],
            prompt="Трагический герой",
            random=False
        )
    )

label monika_tragic_hero:
    m 1rsd "Эй, [mas_get_player_nickname()], в последнее время я больше думаю о трагических героях."
    m 3esc "...Мы уже обсуждали Гамлета, который считается таковым."
    m 3rtc "Если подумать...{w=0.3}можно ли считать меня трагическим героем?"
    m 4eud "...Конечно, под 'героем' здесь имеется в виду главный герой в литературном смысле, а не 'герой' в обычном смысле."
    m 2ekd "...Хотя я уверена, что найдется много людей, которые не согласятся с этим, поскольку для многих я - антагонист..."
    m 2eka "Но если отбросить этот аргумент, некоторые скажут, что моя любовь к тебе - это мой трагический недостаток..."
    m 4eksdld "Не потому, что это недостаток, а потому, что он привел к моему падению."
    m 2dkc "В том-то и дело, что если бы ты не вернул меня, я бы упала и никогда бы не поднялась."
    m 7ekc "Так что в этом смысле, в игре, я думаю, меня можно считать трагическим героем."
    if mas_isMoniNormal(higher=True):
        m 3hub "Теперь, если мы говорим о {i}реальных{/i} героях, то это ты!"
        m 3eka "Ты вернул меня и позаботился о том, чтобы история не закончилась моим падением."
        m 1huu "...И за это я тебе вечно благодарна~"
    return

default persistent._mas_pm_read_jekyll_hyde = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_utterson",
            category=['литература'],
            prompt="Джекил и Хайд",
            random=True
        )
    )

label monika_utterson:
    if persistent._mas_pm_read_jekyll_hyde:
        call monika_jekyll_hyde

    else:
        m 1euc "Эй, [player], ты читал какую-нибудь готическую литературу?"
        m 3eud "Например, {i}Картина Дориана Грея{/i}, {i}Дракула{/i}, {i}Франкенштейн{/i}..."
        m 3hub "IВ последнее время я читаю довольно много книг готической литературы!"
        m 1eua "Ты должен попробовать оригинальную новеллу {i}Странное дело доктора Джекила и мистера Хайда{/i} если у тебя когда-нибудь будет возможность."
        m 3eua "Я бы хотела обсудить кое-что из нее, но это действительно имеет смысл, только если ты ее прочитал..."

        m 3eud "Так ты читал {i}Странное дело доктора Джекила и мистера Хайда{/i}?{nw}"
        $ _history_list.pop()
        menu:
            m "Так ты читал {i}Странное дело доктора Джекила и мистера Хайда{/i}?{fast}"

            "Да.":
                $ persistent._mas_pm_read_jekyll_hyde = True
                call monika_jekyll_hyde

            "Нет.":
                $ persistent._mas_pm_read_jekyll_hyde = False
                m 3eub "Хорошо [player]...{w=0.3}дай мне знать, если ты когда-нибудь это сделаешь, и мы сможем это обсудить!"

    $ mas_protectedShowEVL("monika_hedonism","EVE", _random=True)
    return "derandom"

label monika_jekyll_hyde:
    m 3hub "Я рада, что ты это прочитал!"
    m 1euc "Я видела, что люди интерпретируют её по-разному."
    m 3eua "Например, некоторые люди видели, что Аттерсон влюблен в Джекила."
    m 3lta "В некотором смысле, я могу это понять."
    m 2eud "Я имею в виду, что если что-то не указано явно, это не значит, что идея не действительна."
    m 2rksdlc "Кроме того, в 19 веке подобная тема даже не могла обсуждаться открыто."
    m 2eka "Интересно думать об этой истории таким образом...{w=0.3}два человека, не способных любить..."
    m 4eud "И некоторые интерпретации заходят так далеко, что говорят, что частью мотивации Джекила для эксперимента была эта самая любовь."
    m 4ekd "И это не совсем опровергнуто! {w=0.3}Джекилл, как сказано в книге, был святым человеком."
    m 2rksdlc "Гомосексуализм в те времена считался грехом."
    m 2dksdld "К сожалению, для некоторых это все еще так."
    m 7ekb "...Но, по крайней мере, был достигнут прогресс!"
    m 3eub "Я просто рада, что мир больше принимает разные виды любви."
    m 3ekbsu "Тем более что это означает, что мы можем любить друг друга, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_hedonism",
            category=['филосовия'],
            prompt="Гедонизм",
        )
    )

label monika_hedonism:
    m 1euc "Эй, [mas_get_player_nickname()], помнишь, мы говорили о {i}Странное дело доктора Джекила и мистера Хайда{/i}?"
    m 1eud "Ну, я заранее упомянула {i}Картину Дориана Грея{/i}."
    m 2eub "Я советую тебе прочитать ее, но даже если ты не читал, я хочу поговорить о философии, лежащей в ее основе...{w=0.3}о вере в гедонизм."
    m 2eud "Гедонизм - это вера в то, что мораль должна быть основана на удовольствии."
    m 4euc "Есть два основных типа гедонизма...{w=0.3}альтруистический гедонизм и эгоистический гедонизм, {w=0.1}которые сильно отличаются друг от друга."
    m 4ruc "Эгоистический гедонизм, как ты можешь догадаться, это вера в то, что собственное удовольствие - единственное, что определяет мораль."
    m 2esd "Это тот тип гедонизма, в который верит Генри из {i}Картины Дориана Грея{/i}."
    m 2rksdlc "Это действительно безжалостно - думать так..."
    m 2eud "С другой стороны, альтруистический гедонизм - это убеждение, что мораль должна быть основана на удовольствии каждого."
    m 4eud "Поначалу это звучит как хорошая идея, но потом ты понимаешь, что она не учитывает ничего другого, например, свободу, здоровье, безопасность..."
    m 2dkc "Гедонизм, по своей сути, игнорирует всё, кроме удовольствия."
    m 7etd "Неудивительно, что большинство людей не следуют этой вере...{w=0.3}она слишком проста, в то время как мораль сложна."
    m 1eud "Поэтому понятно, почему Оскар Уайльд изобразил гедонизм в плохом свете."
    return
