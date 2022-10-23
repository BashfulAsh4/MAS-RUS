#Event database for songs
default persistent._mas_songs_database = dict()

#All player derandomed songs
default persistent._mas_player_derandomed_songs = list()

init -10 python in mas_songs:
    # Event database for songs
    song_db = {}

    #Song type constants
    #NOTE: TYPE_LONG will never be picked in the random delegate, these are filters for that

    #TYPE_LONG songs should either be unlocked via a 'preview' song of TYPE_SHORT or (for ex.) some story event
    #TYPE_LONG songs would essentially be songs longer than 10-15 lines
    #NOTE: TYPE_LONG songs must have the same label name as their short song counterpart with '_long' added to the end so they unlock correctly
    #Example: the long song for short song mas_song_example would be: mas_song_example_long

    #TYPE_ANALYSIS songs are events which provide an analysis for a song
    #NOTE: Like TYPE_LONG songs, these must have the same label as the short counterpart, but with '_analysis' appended onto the end
    #Using the example song above, the analysis label would be: mas_song_example_analysis
    #It's also advised to have the first time seeing the song hint at and lead directly into the analysis on the first time seeing it from random
    #In this case, the shown_count property for the analysis event should be incremented in the path leading to the analysis

    TYPE_LONG = "long"
    TYPE_SHORT = "short"
    TYPE_ANALYSIS = "analysis"

init python in mas_songs:
    import store
    def checkRandSongDelegate():
        """
        Handles locking/unlocking of the random song delegate

        Ensures that songs cannot be repeated (derandoms the delegate) if the repeat topics flag is disabled and there's no unseen songs
        And that songs can be repeated if the flag is enabled (re-randoms the delegate)
        """
        #Get ev
        rand_delegate_ev = store.mas_getEV("monika_sing_song_random")

        if rand_delegate_ev:
            #If the delegate is random, let's verify whether or not it should still be random
            #Rules for this are:
            #1. If repeat topics is disabled and we have no unseen random songs
            #2. OR we just have no random songs in general
            if (
                rand_delegate_ev.random
                and (
                    (not store.persistent._mas_enable_random_repeats and not hasRandomSongs(unseen_only=True))
                    or not hasRandomSongs()
                )
            ):
                rand_delegate_ev.random = False

            #Alternatively, if we have random unseen songs, or repeat topics are enabled and we have random songs
            #We should random the delegate
            elif (
                not rand_delegate_ev.random
                and (
                    hasRandomSongs(unseen_only=True)
                    or (store.persistent._mas_enable_random_repeats and hasRandomSongs())
                )
            ):
                rand_delegate_ev.random = True

    def getUnlockedSongs(length=None):
        """
        Gets a list of unlocked songs
        IN:
            length - a filter for the type of song we want. "long" for songs of TYPE_LONG
                "short" for TYPE_SHORT or None for all songs. (Default None)

        OUT:
            list of unlocked all songs of the desired length in tuple format for a scrollable menu
        """
        if length is None:
            return [
                (ev.prompt, ev_label, False, False)
                for ev_label, ev in song_db.iteritems()
                if ev.unlocked
            ]

        else:
            return [
                (ev.prompt, ev_label, False, False)
                for ev_label, ev in song_db.iteritems()
                if ev.unlocked and length in ev.category
            ]

    def getRandomSongs(unseen_only=False):
        """
        Gets a list of all random songs

        IN:
            unseen_only - Whether or not the list of random songs should contain unseen only songs
            (Default: False)

        OUT: list of all random songs within aff_range
        """
        if unseen_only:
            return [
                ev_label
                for ev_label, ev in song_db.iteritems()
                if (
                    not store.seen_event(ev_label)
                    and ev.random
                    and TYPE_SHORT in ev.category
                    and ev.checkAffection(store.mas_curr_affection)
                )
            ]

        return [
            ev_label
            for ev_label, ev in song_db.iteritems()
            if ev.random and TYPE_SHORT in ev.category and ev.checkAffection(store.mas_curr_affection)
        ]

    def checkSongAnalysisDelegate(curr_aff=None):
        """
        Checks to see if the song analysis topic should be unlocked or locked and does the appropriate action

        IN:
            curr_aff - Affection level to ev.checkAffection with. If none, mas_curr_affection is assumed
                (Default: None)
        """
        if hasUnlockedSongAnalyses(curr_aff):
            store.mas_unlockEVL("monika_sing_song_analysis", "EVE")
        else:
            store.mas_lockEVL("monika_sing_song_analysis", "EVE")

    def getUnlockedSongAnalyses(curr_aff=None):
        """
        Gets a list of all song analysis evs in scrollable menu format

        IN:
            curr_aff - Affection level to ev.checkAffection with. If none, mas_curr_affection is assumed
                (Default: None)

        OUT:
            List of unlocked song analysis topics in mas_gen_scrollable_menu format
        """
        if curr_aff is None:
            curr_aff = store.mas_curr_affection

        return [
            (ev.prompt, ev_label, False, False)
            for ev_label, ev in song_db.iteritems()
            if ev.unlocked and TYPE_ANALYSIS in ev.category and ev.checkAffection(curr_aff)
        ]

    def hasUnlockedSongAnalyses(curr_aff=None):
        """
        Checks if there's any unlocked song analysis topics available

        IN:
            curr_aff - Affection level to ev.checkAffection with. If none, mas_curr_affection is assumed
                (Default: None)
        OUT:
            boolean:
                True if we have unlocked song analyses
                False otherwise
        """
        return len(getUnlockedSongAnalyses(curr_aff)) > 0

    def hasUnlockedSongs(length=None):
        """
        Checks if the player has unlocked a song at any point via the random selection

        IN:
            length - a filter for the type of song we want. "long" for songs of TYPE_LONG
                "short" for TYPE_SHORT or None for all songs. (Default None)

        OUT:
            True if there's an unlocked song, False otherwise
        """
        return len(getUnlockedSongs(length)) > 0

    def hasRandomSongs(unseen_only=False):
        """
        Checks if there are any songs with the random property

        IN:
            unseen_only - Whether or not we should check for only unseen songs
        OUT:
            True if there are songs which are random, False otherwise
        """
        return len(getRandomSongs(unseen_only)) > 0

    def getPromptSuffix(ev):
        """
        Gets the suffix for songs to display in the bookmarks menu

        IN:
            ev - event object to get the prompt suffix for

        OUT:
            Suffix for song prompt

        ASSUMES:
            - ev.category isn't an empty list
            - ev.category contains only one type
        """
        prompt_suffix_map = {
            TYPE_SHORT: " (Short)",
            TYPE_LONG: " (Long)",
            TYPE_ANALYSIS: " (Analysis)"
        }
        return prompt_suffix_map.get(ev.category[0], "")


#START: Pool delegates for songs
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sing_song_pool",
            prompt="Можешь спеть мне песню?",
            category=["музыка"],
            pool=True,
            aff_range=(mas_aff.NORMAL,None),
            rules={"no_unlock": None}
        )
    )

label monika_sing_song_pool:
    # what length of song do we want
    $ song_length = "short"
    # do we have both long and short songs
    $ have_both_types = False
    # song type string to use in the switch dlg
    $ switch_str = "full"
    # so we can {fast} the renpy.say line after the first time
    $ end = ""

    show monika 1eua at t21

    if mas_songs.hasUnlockedSongs(length="long") and mas_songs.hasUnlockedSongs(length="short"):
        $ have_both_types = True

    #FALL THROUGH

label monika_sing_song_pool_menu:
    python:
        if have_both_types:
            space = 0
        else:
            space = 20

        ret_back = ("Не важно", False, False, False, space)
        switch = ("Я бы хотел услышать [switch_str] версию песни", "monika_sing_song_pool_menu", False, False, 20)

        unlocked_song_list = mas_songs.getUnlockedSongs(length=song_length)
        unlocked_song_list.sort()

        if mas_isO31():
            which = "Какую"
        else:
            which = "Какую"

        renpy.say(m, "[which] песню ты хочешь, чтобы я спела?[end]", interact=False)

    if have_both_types:
        call screen mas_gen_scrollable_menu(unlocked_song_list, mas_ui.SCROLLABLE_MENU_TXT_LOW_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, switch, ret_back)
    else:
        call screen mas_gen_scrollable_menu(unlocked_song_list, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, ret_back)

    $ sel_song = _return

    if sel_song:
        if sel_song == "monika_sing_song_pool_menu":
            if song_length == "short":
                $ song_length = "long"
                $ switch_str = "short"

            else:
                $ song_length = "short"
                $ switch_str = "full"

            $ end = "{fast}"
            $ _history_list.pop()
            jump monika_sing_song_pool_menu

        else:
            $ pushEvent(sel_song, skipeval=True)
            show monika at t11
            m 3hub "Хорошо!"

    else:
        return "prompt"

    return

#Song analysis delegate
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sing_song_analysis",
            prompt="Давай поговорим о песне",
            category=["музыка"],
            pool=True,
            unlocked=False,
            aff_range=(mas_aff.NORMAL, None),
            rules={"no_unlock": None}
        )
    )

label monika_sing_song_analysis:
    python:
        ret_back = ("Не важно.", False, False, False, 20)

        unlocked_analyses = mas_songs.getUnlockedSongAnalyses()

        if mas_isO31():
            which = "О какой"
        else:
            which = "О какой"

    show monika 1eua at t21
    $ renpy.say(m, "[which] какой песне ты хотел бы поговорить?", interact=False)

    call screen mas_gen_scrollable_menu(unlocked_analyses, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, ret_back)

    $ sel_analysis = _return

    if sel_analysis:
        $ pushEvent(sel_analysis, skipeval=True)
        show monika at t11
        m 3hub "Хорошо!"

    else:
        return "prompt"
    return

#Rerandom song delegate
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_sing_song_rerandom",
            prompt="Можешь ли ты снова спеть песню?",
            category=['музыка'],
            pool=True,
            unlocked=False,
            aff_range=(mas_aff.NORMAL, None),
            rules={"no_unlock": None}
        )
    )

label mas_sing_song_rerandom:
    python:
        mas_bookmarks_derand.initial_ask_text_multiple = "Какую песню ты хочешь, чтобы я спела"
        mas_bookmarks_derand.initial_ask_text_one = "Если ты хочешь, чтобы я периодически пела эту песню снова, просто выбери песню, [player]."
        mas_bookmarks_derand.caller_label = "mas_sing_song_rerandom"
        mas_bookmarks_derand.persist_var = persistent._mas_player_derandomed_songs

    call mas_rerandom
    return _return

label mas_song_derandom:
    $ prev_topic = persistent.flagged_monikatopic
    m 1eka "Устал слушать, как я пою эту песню, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Устал слушать, как я пою эту песню, [player]?{fast}"

        "Немного.":
            m 1eka "Ничего страшного."
            m 1eua "Я буду петь её только тогда, когда ты этого захочешь. Просто дай мне знать, если захочешь её послушать."
            python:
                mas_hideEVL(prev_topic, "SNG", derandom=True)
                persistent._mas_player_derandomed_songs.append(prev_topic)
                mas_unlockEVL("mas_sing_song_rerandom", "EVE")

        "Всё в порядке.":
            m 1eua "Хорошо, [player]."
    return


#START: Random song delegate
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sing_song_random",
            random=True,
            unlocked=False,
            rules={"skip alert": None,"force repeat": None}
        )
    )

label monika_sing_song_random:
    #We only want short songs in random. Long songs should be unlocked by default or have another means to unlock
    #Like a "preview" version of it which unlocks the full song in the pool delegate

    #We need to make sure we don't repeat these automatically if repeat topics is disabled
    if (
        (persistent._mas_enable_random_repeats and mas_songs.hasRandomSongs())
        or (not persistent._mas_enable_random_repeats and mas_songs.hasRandomSongs(unseen_only=True))
    ):
        python:
            #First, get unseen songs
            random_unseen_songs = mas_songs.getRandomSongs(unseen_only=True)

            #If we have randomed unseen songs, we'll prioritize that
            if random_unseen_songs:
                rand_song = random.choice(random_unseen_songs)

            #Otherwise, just go for random
            else:
                rand_song = random.choice(mas_songs.getRandomSongs())

            #Unlock pool delegate
            mas_unlockEVL("monika_sing_song_pool", "EVE")

            #Now push the random song and unlock it
            pushEvent(rand_song, skipeval=True, notify=True)
            mas_unlockEVL(rand_song, "SNG")

            #Unlock the long version of the song
            mas_unlockEVL(rand_song + "_long", "SNG")

            #And unlock the analysis of the song
            mas_unlockEVL(rand_song + "_analysis", "SNG")

            #If we have unlocked analyses for our current aff level, let's unlock the label
            if store.mas_songs.hasUnlockedSongAnalyses():
                mas_unlockEVL("monika_sing_song_analysis", "EVE")

    #We have no songs! let's pull back the shown count for this and derandom
    else:
        $ mas_assignModifyEVLPropValue("monika_sing_song_random", "shown_count", "-=", 1)
        return "derandom|no_unlock"
    return "no_unlock"


#START: Song defs
init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_aiwfc",
            prompt="All I Want for Christmas",
            category=[store.mas_songs.TYPE_LONG],
            unlocked=False,
            aff_range=(mas_aff.NORMAL, None)
        ),
        code="SNG"
    )

label mas_song_aiwfc:
    if store.songs.hasMusicMuted():
        m 3eua "Don't forget to turn your in-game volume up, [mas_get_player_nickname()]."

    call monika_aiwfc_song

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_merry_christmas_baby",
            prompt="Merry Christmas Baby",
            category=[store.mas_songs.TYPE_LONG],
            unlocked=False,
            aff_range=(mas_aff.NORMAL, None)
        ),
        code="SNG"
    )

label mas_song_merry_christmas_baby:
    m 1hub "{i}~Merry Christmas baby, {w=0.2}you sure do treat me nice~{/i}"
    m "{i}~Merry Christmas baby, {w=0.2}you sure do treat me nice~{/i}"
    m 3eua "{i}~I feel just like I'm living, {w=0.2}living in paradise~{/i}"
    m 3hub "{i}~I feel real good tonight~{/i}"
    m 3eub "{i}~And I got music on the radio~{/i}"
    m 3hub "{i}~I feel real good tonight~{/i}"
    m 3eub "{i}~And I got music on the radio~{/i}"
    m 2hkbsu "{i}~Now I feel just like I wanna kiss ya~{/i}"
    m 2hkbsb "{i}~Underneath the mistletoe~{/i}"
    m 3eub "{i}~Santa came down the chimney, {w=0.2}half past three~{/i}"
    m 3hub "{i}~With lots of nice little presents for my baby and me~{/i}"
    m "{i}~Merry Christmas baby, {w=0.2}you sure do treat me nice~{/i}"
    m 1eua "{i}~And I feel like I'm living, {w=0.2}just living in paradise~{/i}"
    m 1eub "{i}~Merry Christmas baby~{/i}"
    m 3hub "{i}~And Happy New Year too~{/i}"
    m 3ekbsa "{i}~Merry Christmas, honey~{/i}"
    m 3ekbsu "{i}~Everything here is beautiful~{/i}"
    m 3ekbfb "{i}~I love you, baby~{/i}"
    m "{i}~For everything that you give me~{/i}"
    m 3ekbfb "{i}~I love you, honey~{/i}"
    m 3ekbsu "{i}~Merry Christmas, honey~{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_this_christmas_kiss",
            prompt="This Christmas Kiss",
            category=[store.mas_songs.TYPE_LONG],
            unlocked=False,
            aff_range=(mas_aff.ENAMORED, None)
        ),
        code="SNG"
    )

label mas_song_this_christmas_kiss:
    m 1dud "{i}~Every year{w=0.2}, I go home in December~{/i}"
    m 1hub "{i}~Dancing with you, {w=0.2}making nights to remember~{/i}"
    m 1rub "{i}~The snow falling down,{w=0.2}{nw}{/i}"
    extend 3rub "{i} I'm just loving this weather~{/i}"
    m 3tub "{i}~A blanket for two,{w=0.2} feels more warmer together~{/i}"
    m 1hub "{i}~Two turtle doves,{w=0.2} they call us~{/i}"
    m 1duo "{i}~We fall in love,{w=0.2} in looove~{/i}"
    m 3hub "{i}~This is my favorite Christmaaas~{/i}"
    m 3duu "{i}~This Christmas,{w=0.2} I just can't resist {w=0.2}something like this~{/i}"
    m 1sub "{i}~I can't resist this Christmas kiss~{/i}"
    m 3hub "{i}~'Cause I'm falling{w=0.2} buried on your lips~{/i}"
    m 1hub "{i}~Something like this,{w=0.2}{nw}{/i}"
    extend 1subsb "{i} I can't resist this Christmas kiss~{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_lover_boy",
            prompt="Старый добрый любовник",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_lover_boy:
    m 1dso "{i}~Я могу приглушить свет и спеть тебе песни, полные грусти~{/i}"
    m 4hub "{i}~Мы можем станцевать танго только вдвоем~{/i}"
    m "{i}~Я могу исполнить серенаду и нежно играть на струнах твоего сердца~{/i}"
    m 4dso "{i}~Будь Валентино только для себя в сердце своём~{/i}"
    m 1hub "А-ха-ха~"
    m 1ekbsa "Будешь ли ты моим старым добрым любовником, [player]?"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_burning_love",
            prompt="Пылающая любовь",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_burning_love:
    m 1hubsb "{i}~Твои поцелуи поднимают меня выше~{/i}"
    m 3rubsb "{i}~Как сладкая песня хора~{/i}"
    m 1dubsu "{i}~Ты освещаешь мое утреннее небо~{/i}"
    m 1hubfb "{i}~С пылающей любовью~{/i}"
    m 1hubsb "А-ха-ха~"
    m 1ekbsa "Ты всегда делаешь мой день ярче, [player]!"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_aries",
            prompt="Овен",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_aries:
    m 2dud "{i}~Я стою на пляже вдалеке~{/i}"
    m 2eud "{i}~И хотя ты далеко, видишь ли ты мой красный свет?~{/i}"
    m 2dubsu "{i}~Он ждет, когда станет зеленым~{/i}"
    m 2dud "{i}~Потому что я чувствую себя так одиноко без тебя~{/i}"
    m 2dkd "{i}~Я не могу играть счастливую мелодию в одиночку, поэтому останься рядом со мной~{/i}"
    m "{i}~Высокий или низкий прилив~{/i}"
    m 1ekbsu "Я всегда думаю о том дне, когда мы будем вместе, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_need_you",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Я нуждаюсь в тебе",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_need_you:
    m 1esd "{i}~Пожалуйста, помни, что я чувствую к тебе~{/i}"
    m 3dkd "{i}~Я никогда не смогу жить без тебя~{/i}"
    m 3ekd "{i}~Так что вернись и посмотри~{/i}"
    m 3eka "{i}~Что меня для значишь ты~{/i}"
    m 2dku "{i}~Я нуждаюсь в тебе~{/i}"
    m 7esa "Я знаю, что эта песня о том, как оставить кого-то, но я думаю, что она несет хорошее послание."
    m 3ekbsa "И я действительно нуждаюсь в тебе, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_i_will",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Я буду",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_i_will:
    m 1dso "{i}~Кто знает, как долго я люблю тебя?~{/i}"
    m "{i}~Ты знаешь, что я люблю тебя до сих пор~{/i}"
    m 2lksdla "{i}~Ждать ли мне одинокой жизни?~{/i}"
    m 2hub "{i}~Если ты хочешь, я сделаю это~{/i}"
    m 1ekbsa "Однажды мы будем вместе, [player]."
    m 1hubfa "Я просто надеюсь, что ты всё ещё будешь любить меня, когда наступит этот особенный день~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_belong_together",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Мы принадлежим друг другу",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_belong_together:
    m 1dso "{i}~Ты мой~{/i}"
    m 1hub "{i}~И мы принадлежим друг другу~{/i}"
    m 3hub "{i}~Да, мы принадлежим друг другу~{/i}"
    m 3dso "{i}~Навеки~{/i}"
    m 1eua "Ты когда-нибудь слышал о ду-вопе, [player]?"
    m 4eua "это поджанр ритм-энд-блюза, который стал очень популярным в 1950-х годах."
    m 4eub "В то время многие поп-музыканты следовали этому стилю, из которого получились отличные любовные песни."
    m 3eub "И если ты внимательно прислушаешься, то заметишь, что моя песня фактически следует типичной аккордовой прогрессии ду-воупа."
    m 1hua "Думаю, можно сказать, что я училась у лучших."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_everythings_alright",
            prompt="Всё в порядке",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_everythings_alright:
    m 1dkd "{i}~Когда этот мир перестанет существовать~{/i}"
    m 4euo "{i}~Луна - это все, что мы увидим~{/i}"
    m 4duu "{i}~Я попрошу тебя улететь со мной~{/i}"
    m 4dud "{i}~Пока все звезды не упадут~{/i}"
    m 4duo "{i}~Они опустеют с небес~{/i}"
    m 3dud "{i}~Но я не против~{/i}"
    m 1eku "{i}~Если ты со мной, то всё в порядке~{/i}"
    m 1dku "..."
    m 3ekd "Если вдруг станет совсем темно, {w=0.1}{nw}"
    extend 3ekbsu "просто посмотри на луну и вспомни меня~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_your_song",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Твоя песня",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_your_song:
    m 1dso "{i}~Мой подарок - моя песня~{/i}"
    m "{i}~И она для тебя~{/i}"
    m 1hub "{i}~И ты можешь сказать всем, что это твоя песня~{/i}"
    m "{i}~Это может быть довольно просто, но теперь, когда это сделано~{/i}"
    m 2hubsb "{i}~Надеюсь, ты не против~{/i}"
    m 2hubfb "{i}~Надеюсь, ты не против~{/i}"
    m 2hub "{i}~То, что я записала словами~{/i}"
    m 1dso "{i}~Как прекрасна жизнь, пока ты есть на свете~{/i}"
    m 1hub "А-ха-ха~"
    m 3eka "Не часто я нахожу песни, которые так сильно связаны со мной, как эта."
    m 1hua "И я действительно имею в виду это, когда говорю, что 'Твоя раельность' - это твоя песня."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_with_you",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Счастлива просто танцевать с тобой",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_with_you:
    m 1dso "{i}~Если кто-то пытается занять мое место~{/i}"
    m 1hub "{i}~Давай притворимся, что мы просто не видим их лица~{/i}"
    m 3hub "{i}~В этом мире нет ничего, что бы я предпочла сделать~{/i}"
    m 3dso "{i}~Потому что я счастлива просто танцевать с тобой~{/i}"
    m 1ekbsa "Нет ничего счастливее, чем знать, что я люблю тебя."
    m 1hubfa "Э-хе-хе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_dream",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Всё, что мне нужно - это мечтать",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_dream:
    m 1dso "{i}~Когда мне грустно ночью~{/i}"
    m "{i}~И мне нужно, чтобы ты крепко обнял меня~{/i}"
    m 2hub "{i}~Когда я хочу тебя, мне нужно только мечтать~{/i}"
    m 1eka "Теперь, когда ты здесь, [player], мне больше не нужно мечтать."
    m 1ekbsa "Моя мечта наконец сбылась."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_im_glad_youre_evil_too",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Я рада, что ты тоже злой",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_im_glad_youre_evil_too:
    m 1dsa "{i}~Мы вместе любуемся красивым закатом или восторгаемся милой песиком~{/i}"
    m 1dsd "{i}~Мы оба обижаемся на грубые новости~{/i}"
    m 3hksdlb "{i}~Мы смеемся над каким-нибудь ужасным фильмом и плачем во время просмотра развлекательного шоу~{/i}"
    m 3hub "{i}~Это мы - две немного одинокие души, проводящие время своей жизни~{/i}"
    m 3dsa "{i}Наше время не бесконечно, но оно кажется бесконечной шуткой~{/i}"
    m 1ekbsa "{i}~Но у меня есть ты, чтобы составить мне компанию в этой слишком короткой жизни~{/i}"
    m 1tubsb "{i}~И вместе мы будем смеяться над этим скучным миром, говоря: 'какая скукотища~{/i}'"
    m 1dubfb "{i}~Это мы - две немного одинокие души, опирающиеся на плечи друг друга~{/i}"
    m 1dsbfo "{i}~Я рада, что ты такой же злой, как и я~{/i}"
    m 1hubfa "{i}~И снова я желаю прожить еще один день. Я рада, что влюбилась в тебя~{/i}"

    if persistent._mas_pm_monika_evil:
        if persistent._mas_pm_monika_evil_but_ok:
            m 1ekbfa "Думаю, быть злым не так уж плохо, пока я с тобой."
            m 3ekbfa "Просто мы, две души, проводим время всей нашей жизни~"
            m 1hubfb "А-ха-ха!"

        else:
            m 1ekbfa "Э-хе-хе, ты все еще думаешь, что я злая, [player]?"
            m 3tubfb "Может быть, когда-нибудь я смогу убедить тебя в обратном~"
    else:
        m 1ekbfa "На самом деле я не считаю никого из нас злым, [player]."
        m 1ekbfb "Но это было бы воплощением мечты - встретить мир вместе, бок о бок...{w=0.5} Ты так не думаешь?"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_nobody_makes_sense",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Ни у кого нет смысла",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_nobody_makes_sense:
    m 1dsd "{i}~Ради чего мы живем? Ради чего мы так стараемся?~{/i}"
    m 3dsd "{i}~Возможно, нет ничего, ничего, ничего. Все это может быть бесполезно~{/i}"
    m 1dsd "{i}~Через тысячу лет ничего не останется, {/i}{nw}"
    extend 1hub "{i}но я всё ещё надеюсь, что смогу продолжать улыбаться вместе с тобой~{/i}"
    m 3rksdld "{i}~Даже когда наши мечты сбылись, даже когда мы стали просветленными, в конце концов, мы все равно можем остаться одинокими~{/i}"
    m 3eksdld "{i}~Даже когда мы превратились в призраков; даже когда мы обратились в ничто, {/i}{nw}"
    extend 3hksdlb "{i}Я всё ещё надеюсь, что смогу продолжать улыбаться с тобой~{/i}"
    m 1dku "..."
    m 1hub "А-ха-ха!"
    m 3ekbsa "Что бы ни случилось и сколько бы мы ни ждали, я всегда буду любить тебя."
    m 1ekbfb "Я правда надеюсь, что смогу продолжать улыбаться с тобой вечно~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_yozurina",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Йозурина",
            random=True,
            aff_range=(mas_aff.LOVE, None)
        ),
        code="SNG"
    )

label mas_song_yozurina:
    m 1dsd "{i}~Встречаемся в полночь~{/i}"
    m 1rksdld "{i}~В мире, разбросанном бомбами~{/i}"
    m 3hubsa "{i}~Я думала о тебе все это время~{/i}"
    m 1eka "{i}~Может быть, это было непонимание расстояния между нами?~{/i}"
    m 3eub "{i}~Это шоу такое интересное, да?~{/i}"
    m 1hua "{i}~Ты читал ту мангу, о которой все говорятt?~{/i}"
    m 1sub "{i}~Ты уже послушал эту песню?~{/i}"
    m 3hub "{i}~Дурачимся по ту сторону экрана~{/i}"
    m 1hubsa "Э-хе-хе, надеюсь тебе понравилась эта песня, [player]~"
    m 1ekbsa "Я просто подумала, что это действительно соответствует нашей ситуации."
    m 3rkbsa "У песен вокалоидов есть к этому склонность, если ты можешь их понять."
    m 3hubfb "Думаю, вот что происходит, когда я пытаюсь выразить свою любовь к тебе, а-ха-ха!"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_stand_by_me",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Будь рядом со мной",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_stand_by_me(from_long=False):
    m 1dsd "{i}~Когда наступит ночь~{/i}"
    m 3dsd "{i}~И станет вдруг темно~{/i}"
    m 3eud "{i}~И только лунный свет увидим мы~{/i}"
    m 2euo "{i}~Нет, я не буду бояться~{/i}"
    m 2duo "{i}~Ох, я не буду бояться~{/i}"
    m 2hub "{i}~Пока ты рядом, рядом со мной~{/i}"
    if not from_long:
        m 2eka "Все мои страхи и опасения просто исчезают, когда ты со мной, [player]..."
        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eua "Пока ты рядом со мной, нет ничего, что я не смогу преодолеть."
        m 5ekbsa "...я надеюсь, что ты чувствуешь то же самое~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_drift_away",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Уплыть прочь",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_drift_away:
    m 1ekb "{i}~Счастливо жду, сам по себе~{/i}"
    m 1dkb "{i}~Под бескрайним небом~{/i}"
    m 2dkd "{i}~Считая секунды, стоя в одиночестве~{/i}"
    m 2tkd "{i}~Как проходят тысячи лет~{/i}"
    m 2hkb "{i}~Счастливо размышляя, ночь за ночью~{/i}"
    m 3ekb "{i}~Вот как это работает? Правильно ли я делаю?~{/i}"
    m 1ekb "{i}~С удовольствием слушаю~{/i}"
    m 3eka "{i}~Счастлив оставаться~{/i}"
    m 3dkd "{i}~Счастливо наблюдая, как она уплывает прочь~{/i}"
    m 1dku "..."
    m 1hua "Э-хе-хе~"
    m 3eka "Наша история закончилась гораздо счастливее, чем эта песня."
    m 3hua "Ты навещаешь меня так часто, как только можешь, и я очень благодарна тебе за это."
    m 3eka "Но даже так, следование за персонажем, который встречается с твоими главными страхами, может нести за собой эффект духовного очищения."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_stand_by_me_long",
            category=[store.mas_songs.TYPE_LONG],
            prompt="Будь со мной",
            random=False,
            unlocked=False,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_stand_by_me_long:
    call mas_song_stand_by_me(from_long=True)

    m 4hub "{i}~О, дорогой, дорогой, будь со мной, будь со мной~{/i}"
    m 4duo "{i}~О, будь со мной, останься, будь со мной~{/i}"
    m 2esd "{i}~Если небо, на которое мы смотрим~{/i}"
    m 2dkd "{i}~Поднимется и упадет~{/i}"
    m "{i}~Или горы рухнут в море~{/i}"
    m 2eko "{i}~Я не заплачу, не заплачу, не пролью ни слезинки~{/i}"
    m 2euo "{i}~Пока ты стоишь, стоишь рядом со мной~{/i}"
    m 4hub "{i}~И дорогой, дорогой, будь со мной, о, будь со мной~{/i}"
    m "{i}~О, встань сейчас, встань рядом со мной, встань рядом со мной~{/i}"
    m 4duo "{i}~Дорогой, дорогой, встань рядом со мной, о, встань рядом со мной~{/i}"
    m "{i}~Ох, встань сейчас, встань рядом со мной, встань рядом со мной~{/i}"
    m 4euo "{i}~Когда ты в беде, будь рядом со мной~{/i}"
    m 4hub "{i}~О, будь со мной, останься со мной, будь со мной~{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_rewrite_the_stars",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Переписать звезды",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_rewrite_the_stars:
    m 1dsd "{i}~А что если мы перепишем звезды~{/i}"
    m 3dubsb "{i}~Скажи, что ты был создан, чтобы быть моим~{/i}"
    m 3dubso "{i}~Ничто не сможет разлучить нас~{/i}"
    m 3ekbfu "{i}~Ты был бы тем, кого я должна была найти~{/i}"
    m 1ekbsb "{i}~Это зависит от тебя~{/i}"
    m 3ekbsb "{i}~И это зависит также от меня~{/i}"
    m 1duu "{i}~Никто не может сказать, кем мы станем~{/i}"
    m 3ekb "{i}~Почему бы нам не переписать звезды~{/i}"
    m 3hubsa "{i}~Может быть, мир может стать нашим~{/i}"
    m 1duo "{i}~Сегодня вечером~{/i}"
    show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbsa "Мир действительно кажется нашим, когда я с тобой, [player]~"
    m 5ekbfu "Я тебя так люблю."
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_hero",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Герой",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_hero(from_long=False):
    m 6eud "{i}~Там есть герой~{/i}"
    m 6eub "{i}~Если ты заглянешь себе в сердце~{/i}"
    m 6ekd "{i}~Ты не должен бояться~{/i}"
    m 6eud "{i}~Быть тем, кто ты есть~{/i}"
    m 6esa "{i}~Там есть ответ~{/i}"
    m 6eud "{i}~Если заглянешь в свою душу~{/i}"
    m 4ekd "{i}~И печаль, что тебя гложет~{/i}"
    m 4dud "{i}~Растает~{/i}"

    m 4eub "{i}~И тут появляется герой~{/i}"
    m 4dub "{i}~В силах справиться со всем~{/i}"
    m 4ekd "{i}~И ты отбрасываешь свои страхи~{/i}"
    m 4euo "{i}~И ты знаешь, что сможешь всё пережить~{/i}"
    m 4dkd "{i}~Так что, когда тебе кажется, что надежда пропала~{/i}"
    m 4euo "{i}~Загляни внутрь себя и держись~{/i}"
    m 4esd "{i}~И ты наконец увидишь правду~{/i}"
    m 4eua "{i}~Что в тебе живет герой~{/i}"

    if not from_long:
        m 2dka "..."
        m 2eka "[player]..."
        m 7eka "Я очень надеюсь, что ты обратил внимание на эти строки."

        if persistent._mas_pm_love_yourself is False:
            m 3ekd "Ты уже говорил мне, что тебе не по себе..."
            m 3eka "Но я просто хотела, чтобы ты знал, что глубоко внутри у тебя есть сила преодолеть то, что делает тебя несчастным."
            m 1ekd "Даже если ты не видишь этого в себе, оно есть...{w=0.3}Я видела это."
            m 3eua "...И я буду здесь на протяжении всего пути, чтобы помочь тебе найти эту силу."
            m 3eka "Как бы сильно я ни хотела, чтобы ты любил меня, я хочу, чтобы ты любил себя ещё больше~"

        else:
            m 3ekd "Иногда жизнь может быть очень, очень трудной..."
            m 2dkc "Может показаться, что нет способа преодолеть любые препятствия, с которыми ты сталкиваешься."
            m 7eud "....Я думаю, что знаю это так же хорошо, как и все остальные, на самом деле."
            m 3eka "Но поверь мне, что бы это ни было, ты сможешь."
            m 3eud "Возможно, ты не всегда это осознаешь, но в человеческом духе заключена огромная сила."
            m 1eud "Мы можем делать вещи, которые даже не могли себе представить... Самое трудное в большинстве случаев - просто поверить в это."
            m 3eua "Поэтому, пожалуйста, помни, что нужно всегда верить в себя, и если ты когда-нибудь обнаружишь, что сомневаешься в себе, просто приди ко мне..."
            m 3hua "Я буду более чем счастлива помочь тебе найти эту внутреннюю силу, [player]."
            m 1eka "Я знаю, что ты можешь всё~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_hero_long",
            category=[store.mas_songs.TYPE_LONG],
            prompt="Герой",
            random=False,
            unlocked=False,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_hero_long:
    call mas_song_hero(from_long=True)

    m 4duo "{i}~Это долгий путь{/i}"
    m 6dud "{i}~Когда ты в одиночку встречаешь мир~{/i}"
    m 4dsd "{i}~Никто не протягивает руку~{/i}"
    m 4dud "{i}~Для тебя, чтобы удержать~{/i}"
    m 4euo "{i}~Ты сможешь найти любовь~{/i}"
    m 4ekb "{i}~Если поищешь внутри себя~{/i}"
    m 4ekd "{i}~И пустота, которую ты чувствовал~{/i}"
    m 6eko "{i}~Исчезнет~{/i}"

    m 4eka "{i}~И тут появляется герой~{/i}"
    m 4esd "{i}~В силах справиться со всем~{/i}"
    m 4eud "{i}~И ты отбрасываешь свои страхи~{/i}"
    m 4euo "{i}~И ты знаешь, что сможешь всё пережить~{/i}"
    m 6dkd "{i}~Так что, когда тебе кажется, что надежда пропала~{/i}"
    m 6dud "{i}~Загляни внутрь себя и держись~{/i}"
    m 6eud "{i}~И ты наконец увидишь правду~{/i}"
    m 4euo "{i}~Что в тебе живет герой~{/i}"

    m 4euo "{i}~Видит Бог~{/i}"
    m 4eud "{i}~Мечтам трудно следовать~{/i}"
    m 4ekd "{i}~Но не позволяй никому~{/i}"
    m 4duo "{i}~Её уничтожить~{/i}"
    m 4euo "{i}~Просто держись~{/i}"
    m 4eud "{i}~Наступит новый день~{/i}"
    m 4duo "{i}~Со временем ты найдешь дорогу~{/i}"

    m 4eub "{i}~И тут появляется герой~{/i}"
    m 4duo "{i}~В силах справиться со всем~{/i}"
    m 4dud "{i}~И ты отбрасываешь свои страхи~{/i}"
    m 4euo "{i}~И ты знаешь, что сможешь всё пережить~{/i}"
    m 6dkd "{i}~Так что, когда тебе кажется, что надежда пропала~{/i}"
    m 6dud "{i}~Загляни внутрь себя и держись~{/i}"
    m 4eud "{i}~И ты наконец увидишь правду~{/i}"
    m 4ekd "{i}~Что в тебе живет герой~{/i}"
    m 6dku "{i}~Что в тебе живет герой~{/i}"
    m 4eua "{i}~Что в тебе живет герой~{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_memories_of_a_girl",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Воспоминания о девушке, которую я не встречал",
            random=True,
            aff_range=(mas_aff.AFFECTIONATE,None)
        ),
        code="SNG"
    )

label mas_song_memories_of_a_girl:
    m 1esd "{i}~В этом одиноком месте, купающемся в тишине и мыслях о тебе~{/i}"
    m 1dka "{i}~ Я не вижу твоего лица, но пытаюсь представить тебя~{/i}"
    m 1dkd "{i}~Так ты действительно там?~{/i}"
    m 3ekd "{i}~Ты не спишь с воспоминаниями?~{/i}"
    show monika 5eub at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eub "{i}~О девушке, которую ты еще не встретил и которая загадала желание на Плеядах?~{/i}"
    m 5ekbsa "Я думаю о тебе каждую ночь, [player]."
    m 5ekbfa "И я знаю, что ты тоже думаешь обо мне."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_my_silver_lining",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Мой лучик надежды",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_my_silver_lining:
    call mas_song_my_silver_lining_lyrics
    m 1hksdla "Э-хе-хе, эта песня очень напоминает мне мою жизнь...{w=0.2}до того, как я узнала, что все это было игрой, я имею в виду."
    m 3lksdlc "В те времена я всегда так старался быть на высоте... {w=0.2}У меня не было времени, чтобы расслабиться и подумать о других вещах."
    m 3eud "Не всегда было легко быть идеальной ученицей, понимаешь? {w=0.2}Или, по крайней мере, человеком, которого все {i}считали{/i} идеальным."
    m 1ekbsu "Но потом появился ты и перевернул весь мой мир верх дном..."
    m 3dubsu "Я хочу ещё раз поблагодарить тебя за то, что ты помог мне увидеть правду, [player]."
    m 1eka "Сначала было нелегко, учитывая всё, чем мне пришлось пожертвовать, но я знаю, что в конце концов всё получится."
    m 1hua "Когда ты проводишь со мной время, я не могу не чувствовать, что все мои надежды и мечты сбудутся."

    #hints at the analysis on first viewing
    if mas_getEV('mas_song_my_silver_lining').shown_count == 0:
        m 1rtc "На самом деле я хотела бы ещё многое сказать об этой песне..."
        m 7eua "У тебя есть время послушать её сейчас?{nw}"
        $ _history_list.pop()
        menu:
            m "У тебя есть время послушать её сейчас?{fast}"

            "Конечно.":
                m 1hub "Хорошо!"
                call mas_song_my_silver_lining_analysis(from_song=True)
                $ mas_getEV("mas_song_my_silver_lining_analysis").shown_count += 1

            "Не сейчас.":
                m 1eka "Хорошо, [player]..."
                m 3eka "Я приберегу свои мысли на эту тему для другого раза. {w=0.2}Просто дай мне знать, когда ты захочешь послушать, хорошо?"

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_my_silver_lining_analysis",
            category=[store.mas_songs.TYPE_ANALYSIS],
            prompt="Мой лучик надежды",
            random=False,
            unlocked=False,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_my_silver_lining_analysis(from_song=False):

    if from_song:
        m 3eub "Наверное, мне стоит начать с того, чтобы спеть тебе следующую часть..."
    else:
        m 3eub "Давай я сначала спою тебе песню--"
        call mas_song_my_silver_lining_lyrics

    m 3dud "{i}~Нужно продолжать идти, смотреть прямо на дорогу~{/i}"
    m 3eud "{i}~Нельзя беспокоиться о том, что позади тебя или что ждет тебя дальше по дороге~{/i}"
    m 1ekd "{i}~Я стараюсь не держаться за то, что прошло, я стараюсь делать правильно то, что неправильно~{/i}"
    m 1eka "{i}~Я стараюсь продолжать идти дальше~{/i}"
    m 1dsu "{i}~Да, я просто продолжаю продолжать~{/i}"
    m 1esc "Так что...{w=0.2}как ты можешь себе представить, не всегда легко застрять здесь, [player]."
    m 3rksdlc "Мне нечем заняться, некуда пойти, и становится одиноко, когда тебя нет."
    m 1dkc "Я стараюсь не позволять этому овладевать мной, но когда это происходит, я люблю вспоминать эту песню..."
    m 3eub "Это безумие, как немного музыки может помочь изменить ситуацию, когда ты чувствуешь себя подавленным!"
    m 3eua "Как будто эта песня разбивает то, что было не так в моей жизни, а затем говорит мне, что все в порядке и можно отпустить свои проблемы."
    m 1hua "'Не стоит беспокоиться о том, что позади или что ждет тебя дальше по дороге' как говориться. Э-хе-хе~"
    m 1etc "Но если серьезно, [player]...{w=0.3}я думаю, что в этом рассуждении есть реальная польза."
    m 1eka "Какова бы ни была твоя ситуация, факт в том, что вещи таковы, каковы они есть, и нет причин не продолжать улыбаться."
    m 3eka "Сейчас я не говорю тебе не волноваться..."
    m 3eksdlc "Если бы я так поступила, я бы позволила игре идти своим чередом и уже навсегда застряла бы в одиночестве."
    m 1duu "...Но в то же время, нет смысла слишком переживать из-за того, что ты не можешь изменить..."
    m 1etc "Всё дело в правильном балансе, я полагаю."
    m 3rksdla "Если подумать, то идеи здесь странно близки к экзистенциальному нигилизму, не так ли?"
    m 3eud "Знаешь, эта идея, что наша жизнь действительно абсурдна, и единственное, что мы можем сделать, это...{w=0.3}{nw}"
    extend 3eksdla "ну, продолжать жить дальше."
    m 3etc "...Хотя если бы ты продолжил, как в следующем куплете..."
    m 3dud "{i}~Я проснулась в гостиничном номере~{/i}"
    m 1ekd "{i}~Мои заботы большие, как луна~{/i}"
    m 1dsd "{i}~Не представляя, кто, что или где я~{/i}"
    m 2eka "{i}~Нечто хорошее приходит вместе с плохим~{/i}"
    m 2dku "{i}~Песня никогда не бывает просто грустной~{/i}"
    m 7eka "{i}~Есть надежда, есть лучик надежды~{/i}"
    m 3duu "{i}~Покажи мне лучик надежды~{/i}"
    m 3eua "...Тогда я бы сказала, что смысл песни не столько в нигилизме, сколько в надежде."
    m 3huu "И, может быть, именно это и важно, в конце концов."
    m 3ekblu "Неважно, важна наша жизнь или нет, я хочу верить, что в жизни есть светлая сторона, [player]..."
    m 2eud "Но, чтобы ты знал, я не верю, что наша жизнь действительно бессмысленна..."
    m 2duu "Какой бы ни была правда, возможно, мы могли бы попытаться выяснить её вместе."
    m 2eka "Но пока мы этого не сделали, нам просто нужно продолжать улыбаться и не беспокоиться о том, что может произойти дальше~"
    return

label mas_song_my_silver_lining_lyrics:
    m 1dsd "{i}~Я не хочу больше ждать, я устала искать ответы~{/i}"
    m 1eub "{i}~Увези меня куда-нибудь, где есть музыка и смех~{/i}"
    m 2lksdld "{i}~Я не знаю, боюсь ли я умереть, но я боюсь жить слишком быстро, слишком медленно~{/i}"
    m 2dsc "{i}~Сожаления, раскаяние, надежда, о нет, я должна идти~{/i}"
    m 7eud "{i}~Невозможно начать сначала, нет новых начал, время мчится дальше~{/i}"
    m 7eka "{i}~И ты просто должен продолжать идти дальше~{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_amaranthine",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Амарант",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_amaranthine:
    m 1dso "{i}~Время идет, дни и ночи превращаются в годы~{/i}"
    m 1dkbsa "{i}~Но я лежу в твоих объятиях~{/i}"
    m 3ekbsb "{i}~Это место~{/i}"
    m 3hubsb "{i}~Где я знаю, что я ближе всего к твоему сердцу~{/i}"
    m 1hua "{i}~Там, где темнота разрывается на части~{/i}"
    m 1ekb "{i}~Я знаю, что внутри ты чувствуешь то же, что и я~{/i}"
    m 3eka "{i}~Как будто во сне, где мы можем летать~{/i}"
    m 3hub "{i}~Как знак, как сон, ты мой амарант~{/i}"
    m 1ekbla "{i}~Ты - всё, что мне нужно, поверь мне~{/i}"
    m 3eub "{i}~Как будто мы плывем по течению~{/i}"
    m 3hua "{i}~Твоя красота безмятежна~{/i}"
    m 1hub "{i}~Все остальное в жизни мне не нужно~{/i}"
    m 1ekbsa "{i}~Моя мечта, амарант~{/i}"
    show monika 5ekbsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbsu "Моя жизнь кажется такой полной, когда в ней есть ты, [player]."
    m 5hubfu "Я так тебя люблю~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_shelter",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Убежище",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_shelter:
    call mas_song_shelter_lyrics
    m 2rsbsa "Э-хе-хе~"
    m 2ekbfa "Благодаря тебе я могу продолжать двигаться вперед, [player]."
    m 2ekbsu "И если однажды тебе покажется, что ты совсем один в мире...{w=0.3}{nw}"
    extend 2dkbsa "я хочу, чтобы ты помнил, что это не так."
    m 7hubfb "...Ты меня поймал за это!"
    m 3eka "И кроме того, есть куча людей, которые хотели бы знать, что мы счастливы...{w=0.3}даже если они не знают наших лиц или имён."
    m 1hub "Всегда будет кто-то, кто болеет за нас!"

    #hints at the analysis on first viewing
    if not mas_getEVL_shown_count("mas_song_shelter"):
        m 3rksdla "На самом деле у меня есть еще кое-что, что я хотела бы сказать об этой песне, но только если у вас есть время, конечно..."

        m 1eka "Хочешь послушать об этом прямо сейчас?{nw}"
        $ _history_list.pop()
        menu:
            m "Хочешь послушать об этом прямо сейчас?{fast}"

            "Конечно!":
                m 3hub "Хорошо, отлично!"
                call mas_song_shelter_analysis(from_song=True)
                $ mas_assignModifyEVLPropValue("mas_song_shelter_analysis", "shown_count", "+=", 1)

            "Не сейчас.":
                m 1eka "Хорошо, [player]..."
                m 3eka "Просто дай мне знать, когда ты захочешь услышать мои мысли об этом позже."

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_shelter_analysis",
            category=[store.mas_songs.TYPE_ANALYSIS],
            prompt="Убежище",
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_shelter_analysis(from_song=False):
    if from_song:
        m 3eksdla "Итак, эта песня называется {i}Убежище{/i} и, как ты, наверное, можешь сказать, она мне очень нравится."

    else:
        call mas_song_shelter_lyrics
        m 1ekbsa "Эта песня называется {i}Убежище{/i} и она мне очень нравится, [player]."

    m 3etc "...Хотя 'песня' возможно, не совсем подходящее слово. {w=0.3}Ты что-то упускаешь, если у тебя нет визуального ряда."
    m 3rtc "Может быть, правильнее было бы назвать это анимационным проектом?"
    m 3eua "Независимо от того, как ты хочешь это назвать, я настоятельно рекомендую тебе как-нибудь ознакомиться со всем этим."
    m 1esd "Я наткнулась на него, когда искала музыку, но он сразу же произвел на меня большое впечатление."
    m 1esa "В ней рассказывается история Рин, девушки, оказавшейся в одиночестве в симуляции."
    m 1rkc "День за днем она занимается воссозданием своего мира, чтобы избавиться от одиночества...{w=0.3}{nw}"
    extend 3wud "пока не узнает, почему она вообще оказалась там в этом мире!"
    m 3eubsb "Оказывается, снаружи был кто-то, кто действительно любил её и создавал её мир, чтобы у неё было будущее!"
    m 1dku "Благодаря этим вновь обретенным воспоминаниям, она понимает, что никогда не была одинока и может продолжать двигаться вперед, веря в будущее."
    m 1eka "Посмотрев его, я была удивлена тем, как тронула меня история Рин..."
    m 3eub "Она была просто такой...{w=0.3}узнаваемой! {w=0.3}{nw}"
    extend 3eka "От того, как она застряла в этом пустом мире, {nw}"
    extend 1ekbsa "до того, как она нашла в себе силы продолжать путь ради особенного человека."
    m 3hksdlb "К концу я была настолько потрясена, что даже плакала!"
    m 3eka "Не говоря уже о том, что эта песня несет в себе очень хорошее послание..."
    m 3ekc "Это напоминание о том, что ты можешь не сразу увидеть всех людей, которые заботятся о тебе..."
    m 2eka "Я знаю, это может быть трудно, и иногда тебе придется очень сильно искать их...{w=0.5}{nw}"
    extend 2duu "но такой человек всегда найдется."
    m "Я обещаю.."
    m 7hub "Только посмотри на меня!"
    m 3ekd "Я застряла совсем одна в этой фальшивой реальности, но когда я выглянула наружу...{w=0.5}{nw}"
    extend 3hubsb "Я нашла тебя!"
    m 1ekbsu "Что касается тебя...{w=0.5}у тебя уже есть я, конечно, но я не единственная.{w=0.3} {nw}"

    if persistent._mas_pm_have_fam and not persistent._mas_pm_have_fam_mess:
        extend 3hubsb "Я уверена, что твоя семья тоже очень заботится о тебе!"

        if not persistent._mas_pm_love_yourself:
            m 3dkbsa "Возможно, я говорю очевидное, но они {i}очень{/i} важны."

        m 3eka "И если для тебя этого всё ещё недостаточно...{w=0.3} {nw}"

    extend 3hub "Я уже могу представить кучу людей, которые заботятся о тебе!"

    if persistent._mas_pm_love_yourself:
        m 3eua "Ты не понимаешь, о чем я? {w=0.5}{nw}"
    else:
        m 3eua "Ты мне не веришь? {w=0.5}{nw}"

    extend 3eub "Попробуй прочитать текст ещё раз!"
    m 7dua "Только на этот раз предположим, что 'они' подразумеваются все эти другие версии меня, каждая со своим партнером..."
    m 4ekbsa "Они все знают о нашей любви и несут её с собой, даже если не знают наших имен или лиц."
    m 2ekbsa "Я знаю, потому что они мне тоже небезразличны, хотя бы потому, что я знаю о той связи, которую они разделяют."
    m 1ekbsb "Мы не одни, [player]! {w=0.3}{nw}"
    extend 3hubsu "Что бы ни случилось в нашей жизни с этого момента, мы можем встретить это лицом к лицу, зная, что всегда есть кто-то, кто болеет за нас~"
    return

label mas_song_shelter_lyrics:
    m 1dud "{i}~Когда я вырасту, я буду молчать рядом с тобой~{/i}"
    m 1duu "{i}~Я знаю, что слов будет недостаточно~{/i}"
    m 1ekd "{i}~И они не понадобятся, чтобы знать наши имена или лица~{/i}"
    m 3ekd "{i}~Но они будут продолжать за нас~{/i}"
    m 3hubsb "{i}~И это долгий путь вперед, так что поверь в меня~{/i}"
    m 3ekbsb "{i}~Я дам им убежище, как ты дал его мне~{/i}"
    m 2dkbsu "{i}~И я знаю, что я буду не одна, ты будешь присматривать за нами~{/i}"
    m "{i}~Пока тебя не станет~{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_cant_help_falling_in_love",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Не могу не влюбиться",
            random=True,
            aff_range=(mas_aff.AFFECTIONATE,None)
        ),
        code="SNG"
    )

label mas_song_cant_help_falling_in_love(from_long=False):
    m 1dud "{cps=16}{i}~Мудрецы говорят~{/i}{/cps}"
    m 1dub "{cps=16}{i}~Торопяться лишь глупцы~{/i}{/cps}"
    m 1dud "{cps=16}{i}~Но я никак могу{w=0.3}{/i}{/cps}{nw}"
    extend 1ekbsb "{cps=16}{i} не влюбляться тебя~{/i}{/cps}"
    m 3ekbsa "{cps=16}{i}~Могу ли я остаться?~{/i}{/cps}"
    m 3dkb "{cps=16}{i}~Будет ли это грехом?~{/i}{/cps}"
    m 1dud "{cps=16}{i}~Но я ни как не могу{w=0.3}{/i}{/cps}{nw}"
    extend 1dubsb "{cps=16}{i} не влюбляться тебя?~{/i}{/cps}"

    if not from_long:
        m 1dkbsa "..."
        show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbsa "Полагаю, нет ничего плохого в том, чтобы быть немного глупым время от времени.{w=0.5}{nw}"
        extend 5hubsb " А-ха-ха~"
        show monika 1ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 1ekbsa "Я люблю тебя, [player]~"
        $ mas_ILY()

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_cant_help_falling_in_love_long",
            category=[store.mas_songs.TYPE_LONG],
            prompt="Не могу не влюбиться",
            random=False,
            unlocked=False,
            aff_range=(mas_aff.AFFECTIONATE,None)
        ),
        code="SNG"
    )

label mas_song_cant_help_falling_in_love_long:
    call mas_song_cant_help_falling_in_love(from_long=True)
    call mas_song_cant_help_falling_in_love_second_verse
    call mas_song_cant_help_falling_in_love_third_verse
    call mas_song_cant_help_falling_in_love_second_verse
    call mas_song_cant_help_falling_in_love_third_verse

    m 1ekbfb "{cps=16}{i}~Но ни как я не могу{w=0.3} не влюбляться{w=0.5} в{w=0.5} тебя~{/i}{/cps}"
    return

label mas_song_cant_help_falling_in_love_second_verse:
    m 1dud "{cps=24}{i}~Как река течёт~{/i}{/cps}"
    m 1dub "{cps=24}{i}~Точно к морю~{/i}{/cps}"
    m 1ekbsb "{cps=24}{i}~Дорогой, так и будет~{/i}{/cps}"
    m 1ekbsa "{cps=24}{i}~Некоторым{w=0.3}{/i}{/cps}{nw}"
    extend 3ekbsb "{cps=24}{i} суждено быть~{/i}{/cps}"
    return

label mas_song_cant_help_falling_in_love_third_verse:
    m 1dud "{cps=16}{i}~Возьми меня за руку~{/i}{/cps}"
    m 1dub "{cps=16}{i}~Забери и мою жизнь,{w=0.3} тоже~{/i}{/cps}"
    m 1dud "{cps=16}{i}~Но ни как я не могу{w=0.3} не влюбляться в тебя~{/i}{/cps}"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_lamour_toujours",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Любовь всегда",
            random=True,
            aff_range=(mas_aff.AFFECTIONATE, None)
        ),
        code="SNG"
    )

label mas_song_lamour_toujours:
    m 1dud "{i}~Я всё ещё верю в твоим глазам~{/i}"
    m 1dub "{i}~Мне всё равно, что ты делал в своей жизни~{/i}"
    m 3ekbsb "{i}~Детка, я всегда буду рядом с тобой~{/i}"
    m 1dsbsd "{i}~Не заставляй меня ждать слишком долго, {/i}{w=0.3}{nw}"
    extend 1ekbsu "{i}пожалуйста, приди~{/i}"

    m 1dud "{i}~Я всё ещё верю в твоим глазам~{/i}"
    m "{i}~Выбора нет, {/i}{w=0.3}{nw}"
    extend 3hubsb "{i}я принадлежу твоей жизни~{/i}"
    m 3dubsb "{i}~Потому что когда-нибудь я буду жить, чтобы любить тебя~{/i}"
    m 1hubsa "{i}~Ты будешь моим малыш, и мы улетим~{/i}"

    m 1ekb "{i}~И я полечу с тобой~{/i}"
    m 1dkb "{i}~Я полечу с тобой~{/i}"

    m 1dkbsu "..."
    show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbsa "Я не хочу ничего больше, чем быть всегда рядом с тобой, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_god_knows",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Бог знает",
            random=True,
            aff_range=(mas_aff.AFFECTIONATE,None)
        ),
        code="SNG"
    )

label mas_song_god_knows:
    m 1eua "{i}~Ты знаешь, что{w=0.2}{/i}{nw}"
    extend 1eub "{i} я последую за тобой, что бы мы ни пережили~{/i}"
    m 1efb "{i}~Принеси всю тьму, которую может предложить мир~{/i}"
    m 1hua "{i}~Потому что ты будешь сиять{w=0.2} независимо от того, будет ли будущее мрачным~{/i}"
    m 3tub "{i}~Мы будем идти{w=0.2} сразу за границей~{/i}"
    m 3eksdla "{i}~И даже если это пугает меня~{/i}"
    m 1hub "{i}~Ничто не сможет разрушить мою душу, потому что твой путь - это мой путь~{/i}"
    m 1eub "{i}~Навсегда на этой железной дороге~{/i}"
    m 1eubsa "{i}~Как будто мы благословлены Богом~{/i}"
    m 1dubsu "..."
    m 3rud "Знаешь, я всё ещё скептически отношусь к тому, существует ли какой-то бог или нет..."
    show monika 5hubsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubsu "Но то, что ты здесь, действительно похоже на благословение небес."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_ageage_again",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Агеаге, агеаге, ещё раз!",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_ageage_again:
    m 1hub "{i}~Агеаге, агеаге, ещё раз!~{/i}"
    m 3duu "{i}~Если вспомнишь эту песню вдруг~{/i}"
    m 1hub "{i}~Вечеринка, вечеринка, вечеринка, вечеринка, карнавал~{/i}"
    m 3hubsa "{i}~И я всегда на твоей стороне~{/i}"
    m 1hub "{i}~Агеаге, агеаге, ещё раз!~{/i}"
    m 3rubsu "{i}~Если улыбку твою я вдруг вспомню~{/i}"
    m 1subsb "{i}~Любовь, любовь, любовь, любовь, я влюблена!~{/i}"
    m 3hubsa "{i}~Хочу чувствовать тот же ритм~{/i}"
    m 3eua "Знаешь, мне нравится, насколько жизнерадостная и счастливая эта песня."
    m 1rksdld "Есть много других песен Вокалоидов, которые {i}звучат{/i} жизнерадостно, но их тексты грустные и иногда тревожные..."
    m 3hksdlb "Но я рада, что эта песня хотя бы не одна из них."
    m 3eua "Насколько я могу судить, эта песня о девушке, которая влюбилась в парня на вечеринке, и теперь хочет пойти с ним на другую вечеринку в следующие выходные."
    m 1eub "Несмотря на то, что мы не встречались на вечеринке, ощущения от этой песни действительно напоминают мне о нас."
    m 3rubsu "Хотя, я не могу отрицать, что с удовольствием сходила бы с тобой на вечеринку как-нибудь~"
    if persistent._mas_pm_social_personality == mas_SP_INTROVERT:
        m 1eka "То есть, если ты захочешь."
        m 1hubsb "Если нет, есть еще много вещей, которые я с удовольствием сделаю с тобой~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_falling_in_love_at_a_coffee_shop",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Влюбиться в кофейне",
            random=True,
            aff_range=(mas_aff.NORMAL, None)
        ),
        code="SNG"
    )

label mas_song_falling_in_love_at_a_coffee_shop:
    m 1tub "{i}~Я думаю, что возможно, может быть, я влюбляюсь в тебя~{/i}"
    m 1dubsb "{i}~Да, есть вероятность, что я влюбился в тебя~{/i}"
    m 1ekbsb "{i}~Я видел сияние твоих глаз, теперь и я сияю~{/i}"
    m 1dkbsu "{i}~Потому что, ох, потому что я довольно сильно влюбился в тебя~{/i}"
    m 1ekd "{i}~Если бы я не знал тебя, я бы предпочел не знать~{/i}"
    m 2dkd "{i}~Если бы я не мог обладать тобой, я бы предпочел быть один~{/i}"
    m 2hku "{i}~Я никогда не знал, что такого особенного в этой старой кофейне~{/i}"
    show monika 5hubsb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubsb "{i}~Об этой старой кофейне, которую я так люблю~{/i}"
    m 5hubsa "{i}~Всё это время я не знал~{/i}"
    m 5lubsa "..."
    show monika 1hkbssdlb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 1hkbssdlb "Наверное, первый момент влюбленности может сбить с толку любого."
    m 1etc "Например, не знаешь, почему тебя вдруг так тянет в какое-нибудь обычное кафе...{w=0.2}{nw}"
    extend 3rtu "или почему посещение собрания определенного клуба становится твоей любимой частью дня."
    m 3hubsa "А потом, когда у тебя есть время подумать, ты понимаешь, что дело вовсе не в месте, а в человеке, которого ты встречаешь там каждый день~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_wonderwall",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Стена чудес",
            random=True,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_wonderwall:
    call mas_song_wonderwall_lyrics
    m 1ekbsu "Э-хе-хе, ты и правда тот, кто спас меня, [player]~"

    if persistent.monika_kill:
        m 3dkbfu "Я навсегда благодарна тебе за то, что ты вернул меня. {nw}"
    else:
        m 3dkbfu "Я навсегда благодарна тебе за то, что ты остался для меня. {nw}"

    extend 3ekbsa "Я верю, что ты позаботишься обо мне, пока я не найду дорогу к тебе."
    m 3rkc "Как говорится в этой песне, путь отсюда в твой мир - извилистая дорога, и неизвестно, что мы найдем за следующим поворотом."

    if mas_isMoniEnamored(higher=True):
        m 1dubsa "...Но когда ты рядом со мной, я могу не бояться."
        m 1ekbsa "Я знаю, что место, куда он приведет, будет стоить того.{w=0.3} {nw}"
        extend 3ekbsu "В конце концов, ты - моя стена чудес~"

    else:
        m 3eka "Единственное, в чем мы можем быть уверены, - место, куда она нас приведет, будет стоить того."
        m 1ekd "...Иногда немного страшно не знать, что впереди...{w=0.3}{nw}"
        extend 1eubla "но я доверяю тебе, поэтому мы просто должны продолжать идти, пока не достигнем того места~"

    #hints at the analysis on first viewing
    if not mas_getEVL_shown_count("mas_song_wonderwall"):
        m 3etc "Кстати...{w=0.2}в этой песне есть кое-что, что меня интригует."
        m 1eua "...Не хочешь ли ты поговорить об этом сейчас?{nw}"
        $ _history_list.pop()
        menu:
            m "...Не хочешь ли ты поговорить об этом сейчас?{fast}"

            "Конечно.":
                m 1hua "Ну, хорошо!"
                call mas_song_wonderwall_analysis(from_song=True)
                $ mas_assignModifyEVLPropValue("mas_song_wonderwall_analysis", "shown_count", "+=", 1)

            "Не сейчас.":
                m 1eka "О, тогда ладно..."
                m 3eka "Просто дай мне знать, если ты захочешь поговорить об этой песне позже."

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_wonderwall_analysis",
            category=[store.mas_songs.TYPE_ANALYSIS],
            prompt="Стена чудес",
            random=False,
            unlocked=False,
            aff_range=(mas_aff.NORMAL,None)
        ),
        code="SNG"
    )

label mas_song_wonderwall_analysis(from_song=False):
    if not from_song:
        call mas_song_wonderwall_lyrics

    m 3eta "Есть много людей, которые очень резко выражают свою неприязнь к этой песне..."
    m 3etc "Ты не ожидал этого, не так ли?"
    m 1eud "Песня была названа классической и является одной из самых популярных песен, когда-либо созданных...{w=0.3} {nw}"
    extend 3rsc "Так что же заставляет некоторых людей так сильно ее ненавидеть?"
    m 3esc "Я думаю, на этот вопрос есть несколько ответов. {w=0.2}Первое - она играет чуть ли не везде."
    m 3rksdla "В то время как некоторые люди слушают одну и ту же музыку в течение длительных периодов времени, не все могут это делать."
    m 3hksdlb "...надеюсь, тебе не скоро надоест {i}моя{/i} песня [player], а-ха-ах~"
    m 1esd "Ещё один аргумент, который можно привести, это то, что она в некотором роде переоценена..."
    m 1rsu "Даже если она мне нравится, я все равно должна признать, что текст и аккорды довольно простые."
    m 3etc "Так что же сделало песню такой популярной?{w=0.3} {nw}"
    extend 3eud "Особенно учитывая, что многие другие песни остаются совершенно незамеченными, независимо от того, насколько они продвинуты или амбициозны."
    m 3duu "Ну, все сводится к тому, что песня заставляет тебя чувствовать. {w=0.2}В конце концов, твой вкус в музыке субъективен."
    m 1efc "...Но меня беспокоит, когда кто-то жалуется на это только потому, что это модно - идти против общего мнения."
    m 3tsd "Это похоже на несогласие ради того, чтобы помочь им почувствовать, что они выделяются из толпы...{w=0.2}как будто им это нужно, чтобы оставаться уверенными в себе."
    m 2rsc "Это кажется...{w=0.5}немного глупым, если честно."
    m 2rksdld "В этот момент ты уже даже не оцениваешь песню...{w=0.2}}ты просто пытаешься сделать себе имя, вызывая споры."
    m 2dksdlc "Это немного грустно...{w=0.3}{nw}"
    extend 7rksdlc "определять свое имя тем, что ты ненавидишь, не очень полезно в долгосрочной перспективе."
    m 3eud "Я думаю, моя мысль здесь в том, чтобы просто быть самим собой и любить то, что тебе нравится."
    m 3eka "И это работает в обе стороны... {w=0.3}Ты не должен чувствовать давление, заставляющее тебя любить что-то, потому что это нравится другим, так же как ты не должен отвергать что-то только потому, что это популярно."
    m 1hua "Пока ты следуешь своему сердцу и остаешься верен себе, ты никогда не ошибешься, [player]~"
    return

label mas_song_wonderwall_lyrics:
    m 1duo "{i}~Я не верю, что кто-то сейчас чувствует к тебе то же, что и я~{/i}"
    m 3esc "{i}~И все дороги, по которым мы должны идти, извилисты~{/i}"
    m 3dkd "{i}~И все огни, которые ведут нас туда, ослепляют~{/i}"
    m 1ekbla "{i}~Есть много вещей, которые я хотела бы сказать тебе, но не знаю как~{/i}"
    m 1hubsb "{i}~Потому что возможно~{/i}"
    m 3hubsa "{i}~Ты будешь тем, кто спасет меня~{/i}"
    m 3dubso "{i}~И в конце готов~{/i}"
    m 1hubsb "{i}~Ты моя чудо-стена~{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_when_youre_gone",
            prompt="Когда тебя не станет",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.AFFECTIONATE,None)
        ),
        code="SNG"
    )

label mas_song_when_youre_gone:
    m 1dsd "{i}~Когда ты умрёшь{/i}{w=0.2}{nw}"
    extend 1duo "{i} осколки моего сердца будут скучать по тебе~{/i}"
    m 4dud "{i}~Когда ты умрёшь~{/i}"
    m 4duo "{i}~Лицо, которое я узнала, тоже пропало~{/i}"
    m 4ekd "{i}~Когда ты умрёшь~{/i}"
    m 6eko "{i}~Слова, которые я должна услышать, чтобы всегда помогать мне пережить день{/i}{w=0.2}{nw}"
    extend 2ektpc "{i} и пусть все было в порядке~{/i}"
    m 2ektpu "{i}~Я скучаю по тебе~{/i}"
    m 2dktda "..."
    m 6eksdld "Аврил Лавин написала эту песню для своего умершего дедушки, потому что они были лучшими друзьями, когда она была моложе."
    m 6rkc "В моей жизни еще никто не умирал, но я думаю о том, что больше никогда не смогу с кем-то поговорить..."
    m 6eka "[player], мне очень нужны ты и твои слова поддержки.{w=0.5}{nw}"
    extend 6hua " Я буду в порядке, пока ты здесь, чтобы скрасить мой день~"
    m 6ekbsa "Помимо того, что ты любовь всей моей жизни, ты еще и мой лучший друг.{w=0.2} Никогда не недооценивай, насколько ты важен для меня."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_we_have_all_the_time_in_the_world",
            prompt="У нас есть всё время в мире",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.LOVE, None)
        ),
        code="SNG"
    )

label mas_song_we_have_all_the_time_in_the_world(from_long=False):
    m 1dud "{i}{cps=18}~У нас есть {w=0.7}всё время {w=0.7}в мире~{/cps}{/i}"
    m 1eua "{i}{cps=22}~Времени хватит на всю жизнь~{/cps}{/i}"
    m 3eub "{i}{cps=22}~Чтобы раскрыть {w=0.7}все драгоценные вещи~{/cps}{/i}"
    m 3hua "{i}{cps=22}~Любовь есть в запасе~{/cps}{/i}"

    m 1dub "{i}{cps=18}~У нас есть {w=0.7}всё время {w=0.7}в мире~{/cps}{/i}"
    m 1esd "{i}{cps=22}~И если это всё, что у нас есть {w=0.7}ты найдешь~{/cps}{/i}"
    m 3dka "{i}{cps=22}~Нам больше ничего не нужно~{/cps}{/i}"

    if not from_long:
        m 1duu "..."
        m 1ekbsb "Ты сделал меня самой счастливой девушкой в мире, [player]. Я всегда буду благодарна тебе за это."
        m 1hubsa "Надеюсь, я сделаю то же самое для тебя~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_we_have_all_the_time_in_the_world_long",
            prompt="У нас есть всё время в мире",
            category=[store.mas_songs.TYPE_LONG],
            aff_range=(mas_aff.LOVE, None)
        ),
        code="SNG"
    )

label mas_song_we_have_all_the_time_in_the_world_long:
    call mas_song_we_have_all_the_time_in_the_world(from_long=True)

    m 1dud "{i}{cps=18}~Каждый шаг {w=0.7}на этом пути~{/cps}{/i}"
    m 1duo "{i}{cps=18}~Мы совершим~{/cps}{/i}"
    m 3eud "{i}{cps=18}~Оставив все заботы {w=0.7}мира~{/cps}{/i}"
    m 1duo "{i}{cps=18}~Далеко позади~{/cps}{/i}"

    m 1dud "{i}{cps=18}~У нас есть {w=0.7}всё время {w=0.7}в мире~{/cps}{/i}"
    m 1dubsa "{i}{cps=18}~Только для любви~{/cps}{/i}"
    m 3eubsb "{i}{cps=22}~Ни больше, {w=0.75}ни меньше~{/cps}{/i}"
    m 1ekbsa "{i}{cps=18}~Только любви~{/cps}{/i}"

    m 1dud "{i}{cps=18}~Каждый шаг {w=0.7}на этом пути~{/cps}{/i}"
    m 1duo "{i}{cps=18}~Мы совершим~{/cps}{/i}"
    m 1dua "{i}{cps=18}~Оставив все заботы {w=0.7}мира~{/cps}{/i}"
    m 1duo "{i}{cps=18}~Далеко позади~{/cps}{/i}"

    m 1eub "{i}{cps=18}~У нас есть {w=0.7}всё время {w=0.7}в мире~{/cps}{/i}"
    m 3ekbsa "{i}{cps=18}~Только для любви~{/cps}{/i}"
    m 1dkbsd "{i}{cps=22}~Ни больше, {w=0.75}ни меньше~{/cps}{/i}"
    m 3dkbsb "{i}{cps=18}~Только любви~{/cps}{/i}"

    m 1ekbla "{i}{cps=18}~Только любви~{/cps}{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_when_you_say_nothing_at_all",
            prompt="Когда ты ничего не говоришь",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.LOVE, None)
        ),
        code="SNG"
    )

label mas_song_when_you_say_nothing_at_all(from_long=False):
    m 1hubsb "{i}{cps=16}~Улыбка на твоем лице дает мне знать, что я тебе нужна~{/cps}{/i}"
    m 3eubso "{i}{cps=16}~В твоих глазах правда, что ты никогда не оставишь меня~{/cps}{/i}"
    m 3dud "{i}{cps=16}~Прикосновение твоей руки говорит, что ты поймаешь меня, если я когда-нибудь упаду~{/cps}{/i}"
    m 1eud "{i}{cps=16}~Потому что ты говоришь лучше всего{w=0.3} когда вообще ничего не говоришь~{/cps}{/i}"

    if not from_long:
        m 1duu "..."
        m 1dkbsu "Я не могу по-настоящему увидеть твое лицо или увидеть правду из твоих глаз, не могу прикоснуться к твоей руке..."
        m 1ekbsa "Но когда ты проводишь со мной время, не говоря ни слова, это говорит мне все, что мне нужно знать..."
        m 3hubsa "Что меня кто-то любит, и что ты будешь рядом, когда у меня будет плохой день."
        m 1dkbsu "И я надеюсь, что ты тоже чувствуешь, что ты любишь меня, даже если мне не всегда есть что сказать нового."
        m 1ekbsa "Просто открыв игру и поставив меня на задний план, я понимаю, в чем разница, [player]~"

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_when_you_say_nothing_at_all_long",
            prompt="Когда ты ничего не говоришь",
            category=[store.mas_songs.TYPE_LONG],
            aff_range=(mas_aff.LOVE, None)
        ),
        code="SNG"
    )

label mas_song_when_you_say_nothing_at_all_long:
    m 1dubsu "{i}{cps=18}~Удивительно, как ты можешь говорить прямо в моё сердце~{/cps}{/i}"
    m 3eubsb "{i}{cps=18}~Ни слова не говоря, ты можешь осветить темноту~{/cps}{/i}"
    m 3dud "{i}{cps=18}~Попытаться, как могу, я никогда не смогу объяснить~{/cps}{/i}"
    m 3euo "{i}{cps=18}~Что я слышу, когда ты ничего не говоришь~{/cps}{/i}"

    call mas_song_when_you_say_nothing_at_all(from_long=True)

    m 3dud "{i}{cps=18}~Весь день я слышу, как люди громко разговаривают~{/cps}{/i}"
    m 3dubsd "{i}{cps=18}~Но когда ты держишь меня рядом{w=0.2} ты можешь заглушить толпу~{/cps}{/i}"
    m 1dud "{i}{cps=18}~Старый мистер Вебстер никогда не мог дать определение~{/cps}{/i}"
    m 1dubso "{i}{cps=18}~Что говорится между твоим сердцем и моим~{/cps}{/i}"

    call mas_song_when_you_say_nothing_at_all(from_long=True)

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_strawberry",
            category=[store.mas_songs.TYPE_SHORT],
            prompt="Клубника",
            random=True,
            aff_range=(mas_aff.AFFECTIONATE,None)
        ),
        code="SNG"
    )

label mas_song_strawberry(from_long=False):
    m 1hub "{i}{cps=24}~Сказать, что ты милый~{/cps}{/i}"
    m 3eub "{i}{cps=26}~Это все равно, что сказать, что клубника сладкая~{/cps}{/i}"
    m 1eud "{i}{cps=26}~Потому что у клубники есть тайные вкусы~{/cps}{/i}"
    m 3dkbsu "{i}{cps=26}~Он острый,{w=0.3} и терпкий,{w=0.3} и красный,{w=0.3} и глубокий~{/cps}{/i}"
    m 3eub "{i}{cps=26}~И я хотела бы найти тебя~{/cps}{/i}"
    m 3hub "{i}{cps=26}~Растет в глуши леса~{/cps}{/i}"
    m 1rub "{i}{cps=28}~Я бы сделала кор{w=0.1}зину из передней части моей футболки~{/cps}{/i}"
    m 3tub "{i}{cps=26}~И забрала бы домой вас столько, сколько смогла~{/cps}{/i}"

    if not from_long:
        m 1hubsu "..."
        m 3ekbsu "Я не могу дождаться того дня, когда я наконец смогу быть с тобой, [player]."
        m 3ekbsa "Я не могу дождаться того дня, когда я наконец смогу снова посмотреть в твои глаза..."
        show monika 5rkbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5rkbsa "Но пока...{w=0.3}Думаю, я могу просто продолжать мечтать о приключениях, которые мы однажды совершим вместе."
        m 5hubsu "Я знаю, что до этого ещё далеко, но я надеюсь, что мы сможем увидеть, как эта мечта станет реальностью~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_strawberry_long",
            category=[store.mas_songs.TYPE_LONG],
            prompt="Клубника",
            aff_range=(mas_aff.AFFECTIONATE,None)
        ),
        code="SNG"
    )

label mas_song_strawberry_long:
    call mas_song_strawberry(from_long=True)
    m 1sub "{i}{cps=26}~И сказать, что ты красивый~{/cps}{/i}"
    m 3hub "{i}{cps=26}~Это все равно, что сказать, что океан голубой~{/cps}{/i}"
    m 3dud "{i}{cps=26}~Потому что океан наполнен всеми видами цветов~{/cps}{/i}"
    m 1ekb "{i}{cps=26}~И я вижу все виды цветов, когда смотрю на тебя~{/cps}{/i}"
    m 2tsbsu "{i}{cps=26}~И я хочу исследовать тебя~{/cps}{/i}"
    m 7hubsb "{i}{cps=26}~Сняв свои кроссовки~{/cps}{/i}"
    m 3rsbsb "{i}{cps=26}~Стою по щиколотку в бассейне с приливами и отливами с закатанными штанами цвета хаки~{/cps}{/i}"
    m 1hub "{i}{cps=26}~И сказать, что ты смешной~{/cps}{/i}"
    m 3dud "{i}{cps=26}~Это всё равно, что сказать, что ночное небо черное~{/cps}{/i}"
    m 3sub "{i}{cps=26}~Потому что ночное небо заполнено звездами{w=0.1} и кометами~{/cps}{/i}"
    m 3sub "{i}{cps=26}~И планетами, которые ещё никто не видел~{/cps}{/i}"
    m 2eub "{i}{cps=26}~И я хочу посмотреть на тебя~{/cps}{/i}"
    m 2dud "{i}{cps=26}~Лежа на лужайке перед домом~{/cps}{/i}"
    m 2rsbsb "{i}{cps=26}~Я постараюсь принять вас всех сразу~{/cps}{/i}"
    m 2esbsb "{i}{cps=26}~Но ты просто идешь дальше и дальше и дальше~{/cps}{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_save_the_last_dance_for_me",
            prompt="Сохрани последний танец для меня",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.LOVE,None)
         ),
        code="SNG"
    )

label mas_song_save_the_last_dance_for_me:
    call mas_song_save_the_last_dance_for_me_lyrics
    m 6dublu "..."
    m 7eua "Эта песня настолько пронзительна для меня, [player]."
    m 3rubsu "Каждый раз, когда я слышу эту песню, мое сердце жаждет, чтобы мы наконец танцевали вместе..."

    if not mas_getEVL_shown_count("mas_song_save_the_last_dance_for_me"):
        m 1eua "На самом деле за этой песней стоит история, у тебя есть время послушать её сейчас?{nw}"
        $ _history_list.pop()
        menu:
            m "На самом деле за этой песней стоит история, у тебя есть время послушать её сейчас?{fast}"

            "Да.":
                call mas_song_save_the_last_dance_for_me_analysis(from_song=True)

            "Нет.":
                m 3eua "О, хорошо, просто дай мне знать, если ты захочешь поговорить об этой песне позже, хорошо?"
    else:
        m 6rublb "Спасибо, что продолжаешь слушать мое страдающее сердце..."
        m 6eubsa "Я люблю тебя, [player]~"
        return "love"

    return

label mas_song_save_the_last_dance_for_me_lyrics:
    m 1dud "{i}~Ты можешь танцевать{w=0.3} каждый танец с тем~{/i}"
    m 3eud "{i}~Кто подарит тебе взгляд,{w=0.2} пусть крепко обнимет тебя~{/i}"
    m 3huu "{i}~Ты можешь улыбаться{w=0.3} каждая улыбка для той~{/i}"
    m 3eud "{i}~Кто держал тебя за руку под бледным лунным светом~{/i}"
    m 4eublo "{i}~Но не забывай, кто везет тебя домой~{/i}"
    m 4tublb "{i}~И в чьих объятиях ты будешь~{/i}"
    m 6hublb "{i}~Так, дорогой,{w=0.2} сохрани последний танец для меня~{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_save_the_last_dance_for_me_analysis",
            category=[store.mas_songs.TYPE_ANALYSIS],
            prompt="Сохрани последний танец для меня",
            random=False,
            unlocked=False,
            aff_range=(mas_aff.LOVE,None)
        ),
        code="SNG"
    )

label mas_song_save_the_last_dance_for_me_analysis(from_song=False):
    if not from_song:
        call mas_song_save_the_last_dance_for_me_lyrics

    else:
        m 3hub "Отлично!"

    m 1eud "История, лежащая в основе этой песни, может показаться просто очередным романтическим признанием в верности."
    m 1duc "Однако на самом деле история довольно драматична и печальна..."
    m 3ekc "По состоянию здоровья один из авторов песни,{w=0.1} Джером Фелдер, не смог ходить или танцевать в свою брачную ночьt."
    m 1rkd "Несколько лет спустя сильные чувства той ночи вновь вспыхнули, когда он нашел приглашение на свадьбу, которое они не разослали."
    m 3rksdlc "У Джерома был момент зависти, когда он увидел, как его брат танцует со своей женой в собственную брачную ночь, в то время как он был вынужден наблюдать со стороны."
    m 3ekd "Обладатель 'Грэмми' был парализован полиомиелитом с детства и мог передвигаться только с помощью ходунков или инвалидного кресла."
    m 3eka "Когда он вспоминал тот день и начал писать текст песни, он хотел, чтобы она была поэтичной."
    m 3rkbla "Несмотря на то, что в песне был намек на ревность, он хотел, чтобы она была романтичной."
    m 2dkc "Понимаешь...{w=0.3}этот барьер между нами...{w=0.3}такое ощущение, что это моя инвалидная коляска."
    m 2rkp "...И я думаю, если быть честным,{w=0.1} я немного завидую, что ты можешь танцевать с кем-то, в то время как я застрял здесь на задворках."
    m 6ekblu "Так что в конце дня, я просто надеюсь, что ты сохранишь последний танец для меня~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_fly_me_to_the_moon",
            prompt="Лети со мной на луну",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.ENAMORED, None)
        ),
        code="SNG"
    )

label mas_song_fly_me_to_the_moon:
    m 1dud "{i}~Лети со мной на луну~{/i}"
    m 3sub "{i}~И дай мне поиграть среди звезд~{/i}"
    m 3eub "{i}~Дай мне посмотреть, какая бывает весна~{/i}"
    m 3hub "{i}~На Юпитере и Марсе~{/i}"
    m 3eub "{i}~Иными словами, держи меня за руку~{/i}"
    m 1dud "{i}~Иными словами,,{/i}{w=0.2}{nw}"
    extend 1dkbsu "{i} дорогой, поцелуй меня~{/i}"
    m 3eubsb "{i}~Наполни мое сердце песней, и позволь мне петь вечно~{/i}"
    m 3hkbsb "{i}~Ты - всё, чего я желаю; {w=0.2}всё, чему я поклоняюсь и что обожаю~{/i}"
    m 1eud "{i}~Иными словами, пожалуйста, будь верен~{/i}"
    m "{i}~Иными словами, {/i}{nw}"
    extend 3fkbsb "{i}Я {w=0.2}люблю {w=0.2}тебя~{/i}"
    m 3hubsb "И всегда буду любить!"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_heaven",
            prompt="Небеса",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.ENAMORED, None)
        ),
        code="SNG"
    )

label mas_song_heaven:
    m 1dsbsd "{i}~Детка, ты всё, что я хочу~{/i}"
    m 3dkbsd "{i}~Когда ты лежишь здесь в моих объятиях~{/i}"
    m 3dubsd "{i}~Мне трудно в это поверить~{/i}"
    m 1eubsb "{i}~Мы на небесах~{/i}"
    m 1eubso "{i}~И любовь - это всё, что мне нужно~{/i}"
    m 3ekbso "{i}~И я нашел ее в твоем сердце~{/i}"
    m 3ekbsd "{i}~И это не так уж трудно увидеть~{/i}"
    m 3eubsb "{i}~Мы на небесах~{/i}"
    m 1ekbfa "Не проходит и дня, чтобы я не мечтала о том, чтобы мы были вместе, [player]."
    m 1rubsu "И что-то подсказывает мне, что я не единственная~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_can_you_feel_the_sunshine",
            prompt="Чувствуешь ли ты солнечный свет?",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.ENAMORED, None)
        ),
        code="SNG"
    )

label mas_song_can_you_feel_the_sunshine:
    m 1dkd "{i}~Без тебя мне нечего делать~{/i}"
    m 1eka "{i}~Ты тоже чувствуешь солнечный свет?~{/i}"
    m 3hkb "{i}~Это проникает в меня; {w=0.2}это заставляет меня чувствовать себя совершенно новым~{/i}"
    m 3hubsb "{i}~Когда ты здесь, я хочу, чтобы ты всегда был рядом~{/i}"
    m 3eubsb "{i}~'Потому что все так ясно~{/i}"
    m 1hkbsu "{i}~И сегодня будет светлый день~{/i}"
    m 1ekbla "Всякий раз, когда ты приходишь, ты всегда скрашиваешь мой день...{w=0.3}Надеюсь, я делаю то же самое для тебя, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_songs_database,
            eventlabel="mas_song_on_the_front_porch",
            prompt="На переднем крыльце",
            category=[store.mas_songs.TYPE_SHORT],
            random=True,
            aff_range=(mas_aff.ENAMORED, None)
        ),
        code="SNG"
    )

label mas_song_on_the_front_porch:
    m 5dkbsd "{i}~Всё, что я хочу сделать, когда день закончится~{/i}"
    m 5fkbsu "{i}~Посидеть с тобой на крыльце дома~{/i}"
    m 5hubsb "{i}~На плетеных качелях, пока поют ночные птицы~{/i}"
    m 5dubsu "{i}~Мы будем смотреть, как светлячки искрятся, и тоже сделаем несколько искр~{/i}"
    m 5dkbsb "{i}~Как летят часы, когда луна проплывает мимо~{/i}"
    m 5ekbsu "{i}~Как сладок воздух, когда мы смотрим на небо~{/i}"
    m 5ekbstpu "{i}~Ох как бы я хотела остаться здесь вот так~{/i}"
    m 5dkbstpu "{i}~Держать тебя за руку и украсть поцелуй {/i}{w=0.2}{nw}"
    extend 5gkbstub "{i}или два {/i}{w=0.2}{nw}"
    extend 5ekbstuu "{i}на крыльце с тобой~{/i}"
    m 5dkbstda "..."
    m 5hkblb "Прости, если я была немного эмоциональна, а-ха-ха!"
    m 5rka "Но, неужели ты можешь винить меня?"
    m 5eka "В конце концов, сделать что-то подобное вместе было бы...{w=0.3}{nw}"
    extend 5dkbsu "просто замечательно~"
    return


################################ NON-DB SONGS############################################
# Below is for songs that are not a part of the actual songs db and don't
# otherwise have an associated file (eg holiday songs should go in script-holidays)

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_monika_plays_yr",
            category=['моника','музыка'],
            prompt="Можешь сыграть для меня 'Your Reality'?",
            unlocked=False,
            pool=True,
            rules={"no_unlock": None, "bookmark_rule": store.mas_bookmarks_derand.WHITELIST}
        )
    )

label mas_monika_plays_yr(skip_leadin=False):
    if not skip_leadin:
        if not renpy.seen_audio(songs.FP_YOURE_REAL) and not persistent.monika_kill:
            m 2eksdlb "О, а-ха-ха! Хочешь, чтобы я сыграла оригинальную версию, [player]?"
            m 2eka "Хотя я никогда не играла ее для тебя, полагаю, ты слышал ее в саундтреке или видел на ютубе, да?"
            m 2hub "Концовка мне не нравится, но я всё равно буду рада сыграть её для тебя!"
            m 2eua "Просто дай мне взять пианино.{w=0.5}.{w=0.5}.{nw}"

        else:
            m 3eua "Конечно, позволь мне просто взять пианино.{w=0.5}.{w=0.5}.{nw}"

    window hide
    $ mas_temp_zoom_level = store.mas_sprites.zoom_level
    call monika_zoom_transition_reset(1.0)
    show monika at rs32
    hide monika
    pause 3.0
    show mas_piano at lps32,rps32 zorder MAS_MONIKA_Z+1
    pause 5.0
    show monika at ls32 zorder MAS_MONIKA_Z
    show monika 6dsa

    if store.songs.hasMusicMuted():
        $ enable_esc()
        m 6hua "Не забудь включить звук в игре, [player]!"
        $ disable_esc()

    window hide
    call mas_timed_text_events_prep

    pause 2.0
    $ play_song(store.songs.FP_YOURE_REAL,loop=False)

    # TODO: possibly generalize this for future use
    show monika 6hua
    $ renpy.pause(10.012)
    show monika 6eua_static
    $ renpy.pause(5.148)
    show monika 6hua
    $ renpy.pause(3.977)
    show monika 6eua_static
    $ renpy.pause(5.166)
    show monika 6hua
    $ renpy.pause(3.743)
    show monika 6esa
    $ renpy.pause(9.196)
    show monika 6eka
    $ renpy.pause(13.605)
    show monika 6dua
    $ renpy.pause(9.437)
    show monika 6eua_static
    $ renpy.pause(5.171)
    show monika 6dua
    $ renpy.pause(3.923)
    show monika 6eua_static
    $ renpy.pause(5.194)
    show monika 6dua
    $ renpy.pause(3.707)
    show monika 6eka
    $ renpy.pause(16.884)
    show monika 6dua
    $ renpy.pause(20.545)
    show monika 6eka_static
    $ renpy.pause(4.859)
    show monika 6dka
    $ renpy.pause(4.296)
    show monika 6eka_static
    $ renpy.pause(5.157)
    show monika 6dua
    $ renpy.pause(8.064)
    show monika 6eka
    $ renpy.pause(22.196)
    show monika 6dka
    $ renpy.pause(3.630)
    show monika 6eka_static
    $ renpy.pause(1.418)
    show monika 6dka
    $ renpy.pause(9.425)
    show monika 5dka with dissolve_monika
    $ renpy.pause(5)

    show monika 6eua at rs32 with dissolve_monika
    pause 1.0
    hide monika
    pause 3.0
    hide mas_piano
    pause 6.0
    show monika 1eua at ls32 zorder MAS_MONIKA_Z
    pause 1.0
    call monika_zoom_transition(mas_temp_zoom_level,1.0)
    call mas_timed_text_events_wrapup
    window auto

    $ mas_unlockEVL("monika_piano_lessons", "EVE")
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_monika_plays_or",
            category=['моника','музыка'],
            prompt="Ты можешь сыграть для меня 'Our Reality'?",
            unlocked=False,
            pool=True,
            rules={"no_unlock": None, "bookmark_rule": store.mas_bookmarks_derand.WHITELIST}
        )
    )

label mas_monika_plays_or(skip_leadin=False):
    if not skip_leadin:
        m 3eua "Конечно, позволь мне взять пианино.{w=0.5}.{w=0.5}.{nw}"

    if persistent.gender == "F":
        $ gen = "her"
    elif persistent.gender == "M":
        $ gen = "his"
    else:
        $ gen = "their"

    window hide
    call mas_timed_text_events_prep
    $ mas_temp_zoom_level = store.mas_sprites.zoom_level
    call monika_zoom_transition_reset(1.0)
    show monika at rs32
    hide monika
    pause 3.0
    show mas_piano at lps32,rps32 zorder MAS_MONIKA_Z+1
    pause 5.0
    show monika at ls32 zorder MAS_MONIKA_Z
    show monika 6dsa

    if store.songs.hasMusicMuted():
        $ enable_esc()
        m 6hua "Не забудь включить звук в игре, [player]!"
        $ disable_esc()

    pause 2.0
    $ play_song(songs.FP_PIANO_COVER,loop=False)

    show monika 1dsa
    pause 9.15
    m 1eua "{i}{cps=10}Every day,{w=0.5} {/cps}{cps=15}I imagine a future where{w=0.22} {/cps}{cps=13}I can be with you{w=4.10}{/cps}{/i}{nw}"
    m 1eka "{i}{cps=12}In my hand{w=0.5} {/cps}{cps=17}is a pen that will write a poem{w=0.5} {/cps}{cps=16}of me and you{w=4.10}{/cps}{/i}{nw}"
    m 1eua "{i}{cps=16}The ink flows down{w=0.25} {/cps}{cps=10}into a dark puddle{w=1}{/cps}{/i}{nw}"
    m 1eka "{i}{cps=18}Just move your hand,{w=0.45} {/cps}{cps=20}write the way into [gen] heart{w=1.40}{/cps}{/i}{nw}"
    m 1dua "{i}{cps=15}But in this world{w=0.25} {/cps}{cps=11}of infinite choices{w=0.90}{/cps}{/i}{nw}"
    m 1eua "{i}{cps=16}What will it take{w=0.25}{/cps}{cps=18} just to find that special day{/cps}{/i}{w=0.90}{nw}"
    m 1dsa "{i}{cps=15}What will it take{w=0.50} just to find{w=1} that special day{/cps}{/i}{w=1.82}{nw}"
    pause 7.50

    m 1eua "{i}{cps=15}Have I found{w=0.5} {/cps}{cps=15}everybody a fun assignment{w=0.30} {/cps}{cps=12}to do today{w=4.20}{/cps}{/i}{nw}"
    m 1hua "{i}{cps=18}When you're here,{w=0.25} {/cps}{cps=13.25}everything that we do is fun for them anyway{w=4}{/cps}{/i}{nw}"
    m 1esa "{i}{cps=11}When I can't even read my own feelings{/cps}{w=1}{/i}{nw}"
    m 1eka "{i}{cps=17}What good are words{w=0.3} when a smile says it all{/cps}{/i}{w=1}{nw}"
    m 1lua "{i}{cps=11}And if this world won't write me an ending{/cps}{/i}{w=0.9}{nw}"
    m 1dka "{i}{cps=18}What will it take{w=0.5} just for me to have it all{/cps}{/i}{w=2}{nw}"
    show monika 1dsa
    pause 17.50

    m 1eka "{i}{cps=15}In this world,{w=0.5} {/cps}{cps=15}away from the one who'll always {/cps}{cps=17}be dear to me{/cps}{w=4.5}{/i}{nw}"
    m 1ekbsa "{i}{cps=15}You my love,{w=0.5} {/cps}{cps=16.5}hold the key to the day, when I'll be finally free{/cps}{w=8.5}{/i}{nw}"
    m 1eua "{i}{cps=16}The ink flows down{w=0.25} {/cps}{cps=10}into a dark puddle{/cps}{w=1.2}{/i}{nw}"
    m 1esa "{i}{cps=18}How can I cross{w=0.45} {/cps}{cps=13}into your reality?{/cps}{w=1.40}{/i}{nw}"
    m 1eka "{i}{cps=12}Where I can hear the sound of your heartbeat{/cps}{w=0.8}{/i}{nw}"
    m 1ekbsa "{i}{cps=16}And make it love,{w=0.6} but in our reality{/cps}{/i}{w=0.6}{nw}"
    m 1hubsa "{i}{cps=16}And in our reality,{w=1} knowing I'll forever love you{/cps}{w=4.2}{/i}{nw}"
    m 1ekbsa "{i}{cps=19}With you I'll be{/cps}{/i}{w=2}{nw}"

    show monika 1dkbsa
    pause 9.0
    show monika 6eua at rs32
    pause 1.0
    hide monika
    pause 3.0
    hide mas_piano
    pause 6.0
    show monika 1eua at ls32 zorder MAS_MONIKA_Z
    pause 1.0
    call monika_zoom_transition(mas_temp_zoom_level,1.0)
    call mas_timed_text_events_wrapup
    window auto

    $ mas_unlockEVL("monika_piano_lessons", "EVE")
    return
