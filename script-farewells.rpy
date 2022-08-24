##This file contains all of the variations of goodbye that monika can give.
## This also contains a store with a utility function to select an appropriate
## farewell
#
# HOW FAREWELLS USE EVENTS:
#   unlocked - determines if the farewell can actually be shown
#   random - True means the farewell is shown in the randomly selected
#       goodbye option
#   pool - True means the farewell is shown in the goodbye list. Prompt
#       is used in this case.

#Flag to mark if the player stayed up late last night. Kept as a generic name in case it can be used on other farewells/greetings
default persistent.mas_late_farewell = False

init -1 python in mas_farewells:
    import datetime
    import store

    #The label used for the "let me get ready" phase of the io generation
    #(Used by the iostart label)
    dockstat_iowait_label = None

    #The label containing dialogue for when Monika is ready to go out.
    #(Used by the generic iowait label)
    dockstat_rtg_label = None

    #The label containing dialogue used for when you tell Monika you can't take her with you
    #(Used in the generic iowait label)
    dockstat_cancel_dlg_label = None

    #The label used to contain the menu in which Monika asks what's wrong
    #(Used when you click the wait button during iowait)
    dockstat_wait_menu_label = None

    #The label used which contains the menu where Monika asks the player if they're still going to go
    #(Used if you cancel dockstat gen)
    dockstat_cancelled_still_going_ask_label = None

    #The label used which contains the menu where Monika asks the player if they're still going to go
    #(Used in the generic rtg label if we failed to generate a file)
    dockstat_failed_io_still_going_ask_label = None

    def resetDockstatFlowVars():
        """
        Resets all the dockstat flow vars back to the original states (None)
        """
        store.mas_farewells.dockstat_iowait_label = None
        store.mas_farewells.dockstat_rtg_label = None
        store.mas_farewells.dockstat_cancel_dlg_label = None
        store.mas_farewells.dockstat_wait_menu_label = None
        store.mas_farewells.dockstat_cancelled_still_going_ask_label = None
        store.mas_farewells.dockstat_failed_io_still_going_ask_label = None

    def _filterFarewell(
            ev,
            curr_pri,
            aff,
            check_time,
        ):
        """
        Filters a farewell for the given type, among other things.

        IN:
            ev - ev to filter
            curr_pri - current loweset priority to compare to
            aff - affection to use in aff_range comparisons
            check_time - datetime to check against timed rules

        RETURNS:
            True if this ev passes the filter, False otherwise
        """
        # NOTE: new rules:
        #   eval in this order:
        #   1. hidden via bitmask
        #   2. unlocked
        #   3. not pooled
        #   4. aff_range
        #   5. priority (lower or same is True)
        #   6. all rules
        #   7. conditional
        #       NOTE: this is never cleared. Please limit use of this
        #           property as we should aim to use lock/unlock as primary way
        #           to enable or disable greetings.

        # check if hidden from random select
        if ev.anyflags(store.EV_FLAG_HFRS):
            return False

        #Make sure the ev is unlocked
        if not ev.unlocked:
            return False

        #If the event is pooled, then we cannot have this in the selection
        if ev.pool:
            return False

        #Verify we're within the aff bounds
        if not ev.checkAffection(aff):
            return False

        #Priority check
        if store.MASPriorityRule.get_priority(ev) > curr_pri:
            return False

        #Since this event checks out in the other areas, finally we'll evaluate the rules
        if not (
            store.MASSelectiveRepeatRule.evaluate_rule(check_time, ev, defval=True)
            and store.MASNumericalRepeatRule.evaluate_rule(check_time, ev, defval=True)
            and store.MASGreetingRule.evaluate_rule(ev, defval=True)
            and store.MASTimedeltaRepeatRule.evaluate_rule(ev)
        ):
            return False

        #Conditional check (Since it's ideally least likely to be used)
        if not ev.checkConditional():
            return False

        # otherwise, we passed all tests
        return True

    # custom farewell functions
    def selectFarewell(check_time=None):
        """
        Selects a farewell to be used. This evaluates rules and stuff appropriately.

        IN:
            check_time - time to use when doing date checks
                If None, we use current datetime
                (Default: None)

        RETURNS:
            a single farewell (as an Event) that we want to use
        """
        # local reference of the gre database
        fare_db = store.evhand.farewell_database

        # setup some initial values
        fare_pool = []
        curr_priority = 1000
        aff = store.mas_curr_affection

        if check_time is None:
            check_time = datetime.datetime.now()

        # now filter
        for ev_label, ev in fare_db.iteritems():
            if _filterFarewell(
                ev,
                curr_priority,
                aff,
                check_time
            ):
                # change priority levels and stuff if needed
                ev_priority = store.MASPriorityRule.get_priority(ev)
                if ev_priority < curr_priority:
                    curr_priority = ev_priority
                    fare_pool = []

                # add to pool
                fare_pool.append((
                    ev, store.MASProbabilityRule.get_probability(ev)
                ))

        # not having a greeting to show means no greeting.
        if len(fare_pool) == 0:
            return None

        return store.mas_utils.weightedChoice(fare_pool)

# farewells selection label
label mas_farewell_start:
    # TODO: if we ever have another special farewell like long absence
    # that let's the player go after selecting the farewell we'll need
    # to define a system to handle those.
    if persistent._mas_long_absence:
        $ pushEvent("bye_long_absence_2")
        return

    $ import store.evhand as evhand
    # we use unseen menu values

    python:
        # preprocessing menu
        # TODO: consider including processing the rules dict as well

        Event.checkEvents(evhand.farewell_database)

        bye_pool_events = Event.filterEvents(
            evhand.farewell_database,
            unlocked=True,
            pool=True,
            aff=mas_curr_affection,
            flag_ban=EV_FLAG_HFM
        )

    if len(bye_pool_events) > 0:
        # we have selectable options
        python:
            # build a prompt list
            bye_prompt_list = sorted([
                (ev.prompt, ev, False, False)
                for k,ev in bye_pool_events.iteritems()
            ])

            most_used_fare = sorted(bye_pool_events.values(), key=Event.getSortShownCount)[-1]

            #Setup the last options
            final_items = [
                (_("До свидания."), -1, False, False, 20),
                (_("Не важно."), False, False, False, 0)
            ]

            #To manage this, we'll go by aff/anni first, as by now, the user should likely have a pref (also it's like an aff thing)
            #If we still don't have any uses (one long sesh/only uses "goodbye", then we just retain the two options)
            #TODO: Change this with TC-O to adapt to player schedule
            if mas_anni.pastOneMonth() and mas_isMoniAff(higher=True) and most_used_fare.shown_count > 0:
                final_items.insert(1, (most_used_fare.prompt, most_used_fare, False, False, 0))
                _menu_area = mas_ui.SCROLLABLE_MENU_VLOW_AREA

            else:
                _menu_area = mas_ui.SCROLLABLE_MENU_LOW_AREA

        #Call the menu
        call screen mas_gen_scrollable_menu(bye_prompt_list, _menu_area, mas_ui.SCROLLABLE_MENU_XALIGN, *final_items)

        if not _return:
            #Nevermind
            return _return

        if _return != -1:
            $ mas_setEventPause(None)
            #Push the selected event
            $ pushEvent(_return.eventlabel, skipeval=True)
            return

    $ mas_setEventPause(None)
    # otherwise, select a random farewell
    $ farewell = store.mas_farewells.selectFarewell()
    $ pushEvent(farewell.eventlabel, skipeval=True)

    return

###### BEGIN FAREWELLS ########################################################
## FARE WELL RULES:
# unlocked - True means this farewell is ready for selection
# pool - pooled ones are selectable in the menu, if non-pool, it is assumed available in random selection
# rules - Dict containing different rules(check event-rules for more details)
###

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_leaving_already",
            unlocked=True,
            conditional="mas_getSessionLength() <= datetime.timedelta(minutes=20)",
            aff_range=(mas_aff.NORMAL, None)
        ),
        code="BYE"
    )

label bye_leaving_already:
    m 1ekc "О, уже уходишь?"
    m 1eka "Очень грустно, когда тебе приходится уходить..."
    m 3eua "Просто не забудь вернуться, как только сможешь, хорошо?"
    m 3hua "Я так люблю тебя, [player]. Береги себя!"
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_goodbye",
            unlocked=True
        ),
        code="BYE"
    )

label bye_goodbye:
    if mas_isMoniNormal(higher=True):
        m 1eua "До свидания, [mas_get_player_nickname()]!"

    elif mas_isMoniUpset():
        m 2esc "До свидания."

    elif mas_isMoniDis():
        m 6rkc "Ох...{w=1} До свидания."
        m 6ekc "Пожалуйста...{w=1}не забудь вернуться."

    else:
        m 6ckc "..."

    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_sayanora",#sayanora? yes
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None)
        ),
        code="BYE"
    )

label bye_sayanora:
    m 1hua "Сайонара, [mas_get_player_nickname()]~"
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_farewellfornow",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None)
        ),
        code="BYE"
    )

label bye_farewellfornow:
    m 1eka "Прощай, [mas_get_player_nickname()]~"
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_untilwemeetagain",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None)
        ),
        code="BYE"
    )

label bye_untilwemeetagain:
    m 2eka "'{i}Прощание - это не навсегда, Прощание - это не конец. Они просто означают, что я буду скучать по тебе, Пока мы не встретимся снова.{/i}'"
    m "Э-хе-хе, до тех пор, прощай, [mas_get_player_nickname()]!"
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_take_care",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None)
        ),
        code="BYE"
    )


label bye_take_care:
    m 1eua "Не забывай, что я всегда люблю тебя, [mas_get_player_nickname()]~"
    m 1hub "Береги себя!"
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_leaving_already_2",
            unlocked=True,
            aff_range=(mas_aff.HAPPY, None)
        ),
        code="BYE"
    )

label bye_leaving_already_2:
    if mas_getSessionLength() <= datetime.timedelta(minutes=30):
        m 1ekc "Оу, уже уходишь?"
    m 1eka "Очень грустно, когда тебе приходится уходить..."
    m 3hubsa "Я так люблю тебя, [player]!"
    show monika 5hubsb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubsb "Никогда не забывай об этом!"
    return 'quit'

init 5 python:
    rules = dict()
    rules.update(MASSelectiveRepeatRule.create_rule(hours=[0,20,21,22,23]))
    rules.update(MASPriorityRule.create_rule(50))
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_going_to_sleep",
            unlocked=True,
            rules=rules
        ),
        code="BYE"
    )
    del rules

label bye_going_to_sleep:
    #TODO: TC-O things
    if mas_isMoniNormal(higher=True):
        $ p_nickname = mas_get_player_nickname()
        m 1esa "Ты собираешься спать, [p_nickname]?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты собираешься спать, [p_nickname]?{fast}"

            "Да.":
                call bye_prompt_sleep_goodnight_kiss(chance=4)
                # If denied her kiss, quit here
                if _return is not None:
                    return "quit"

                m 7eka "Я встречусь с тобой во сне."

                #Going to sleep, so we should set the greet type and timeout
                $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=13)
                $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SLEEP

            "Нет.":
                m 1eka "Хорошо. {w=0.3}Приятного вечера~"

    elif mas_isMoniUpset():
        m 2esc "Собираешься спать, [player]?"
        m "Спокойной ночи."

    elif mas_isMoniDis():
        m 6rkc "Ох... спокойной ночи, [player]."
        m 6lkc "Надеюсь, увидимся завтра..."
        m 6dkc "Не забывай обо мне, хорошо?"

    else:
        m 6ckc "..."

    # TODO:
    # can monika sleep with you?
    # via flashdrive or something

    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_prompt_to_class",
            unlocked=True,
            prompt="Я иду на занятия.",
            pool=True
        ),
        code="BYE"
    )

label bye_prompt_to_class:
    $ session_time = mas_getSessionLength()
    if mas_isMoniNormal(higher=True):
        if session_time < datetime.timedelta(minutes=20):
            m 1ekd "Оу, уже уходишь?"
            m 1efp "Ты не провел здесь и 20 минут!"
            m 3hksdlb "Я просто шучу, [player]."
            m 2eka "Ты такой милый, что встречаешься со мной, даже когда у тебя так мало времени."
            m 2hub "Я просто хочу, чтобы ты знал, что я очень ценю это!"
            m 2eka "Усердно учись [player], я уверена, у тебя все получится!"
            m 2hua "Увидимся, когда вернешься!"
        elif session_time < datetime.timedelta(hours=1):
            m 2eua "Хорошо, спасибо, что провел со мной немного времени, [player]!"
            m 2eka "Честно говоря, я бы хотела, чтобы это было подольше... но ты занят."
            m 2hua "Нет ничего важнее чем хорошее обучение."
            m 3eub "Научи меня чему-нибудь, когда вернешься!"
            m "До скорой встречи!"
        elif session_time < datetime.timedelta(hours=6):
            m 1hua "Учись усердно, [player]!"
            m 1eua "Нет ничего более привлекательного, чем [guy] с хорошими оценками."
            m 1hua "До встречи!"
        else:
            m 2ekc "М-м-м... ты здесь со мной уже довольно долго, [player]."
            m 2ekd "Ты уверен, что достаточно отдохнул?"
            m 2eka "Убедись, что ты не будешь напрягаться, хорошо?"
            m "Если ты чувствуешь себя не очень хорошо, я уверена, что {i}один день{/i} отдыха не повредит."
            m 1hka "Я буду ждать твоего возвращения. Береги себя."

    elif mas_isMoniUpset():
        m 2esc "Хорошо, [player]."
        m "Надеюсь, сегодня ты хотя бы {i}чему-нибудь{/i} научишься."
        m 2efc "{cps=*2}Например, как лучше относиться к людям.{/cps}{nw}"

    elif mas_isMoniDis():
        m 6rkc "Ох, хорошо [player]..."
        m 6lkc "Думаю, увидимся после школы."

    else:
        m 6ckc "..."
    # TODO:
    # can monika join u at schools?
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SCHOOL
    $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=20)
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_prompt_to_work",
            unlocked=True,
            prompt="Я иду на работу.",
            pool=True
        ),
        code="BYE"
    )

label bye_prompt_to_work:
    $ session_time = mas_getSessionLength()
    if mas_isMoniNormal(higher=True):
        if session_time < datetime.timedelta(minutes=20):
            m 2eka "О, хорошо! Просто проверяешь меня перед выходом?"
            m 3eka "У тебя, должно быть, очень мало времени, если ты уже уходишь."
            m "Было очень мило с твоей стороны увидеть меня, даже когда ты так занят!"
            m 3hub "Трудись, [mas_get_player_nickname()]! Заставь меня гордиться тобой!"
        elif session_time < datetime.timedelta(hours=1):
            m 1hksdlb "О! Хорошо! Я начала чувствовать себя очень комфортно, а-ха-ха."
            m 1rusdlb "Я ожидала, что мы пробудем здесь немного дольше, но ты занятой [guy]!"
            m 1eka "Было здорово увидеть тебя, даже если это было не так долго, как я хотела..."
            m 1kua "Но если бы это зависело от меня, я бы провела с тобой весь день!"
            m 1hua "Я буду здесь ждать, пока ты вернешься с работы!"
            m "Расскажи мне обо всем, когда вернешься!"
        elif session_time < datetime.timedelta(hours=6):
            m 2eua "Собираешься на работу, [mas_get_player_nickname()]?"
            m 2eka "День может быть хорошим или плохим... но если его становится слишком много, подумай о чем-нибудь приятном!"
            m 4eka "Каждый день, как бы плохо он ни проходил, в конце концов заканчивается!"
            m 2tku "Может быть, ты вспомнишь обо мне, если тебе станет тяжело..."
            m 2esa "Просто старайся изо всех сил! Увидимся, когда ты вернешься!"
            m 2eka "Я знаю, что у тебя все получится!"
        else:
            m 2ekc "Ох... Ты здесь уже довольно давно... и теперь ты собираешься работать?"
            m 2rksdlc "Я надеялась, что ты отдохнешь, прежде чем делать что-то серьезное."
            m 2ekc "Постарайся не перенапрягаться, хорошо?"
            m 2ekd "Не бойся сделать перерыв, если понадобится!"
            m 3eka "Просто возвращайся домой ко мне счастливым и здоровым."
            m 3eua "Береги себя, [mas_get_player_nickname()]!"

    elif mas_isMoniUpset():
        m 2esc "Хорошо, [player], думаю, увидимся после работы."

    elif mas_isMoniDis():
        m 6rkc "Ох...{w=1} Хорошо."
        m 6lkc "Надеюсь, тогда увидимся после работы."

    else:
        m 6ckc "..."
    # TODO:
    # can monika join u at work
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_WORK
    $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=20)
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_prompt_sleep",
            unlocked=True,
            prompt="Я собираюсь спать.",
            pool=True
        ),
        code="BYE"
    )

label bye_prompt_sleep:
    if mas_isMoniNormal(higher=True):
        call bye_prompt_sleep_goodnight_kiss(chance=3)
        # Quit if ran the flow
        if _return is not None:
            return "quit"

        m 1eua "Хорошо, [mas_get_player_nickname()]."
        m 1hua "Сладких снов!~"

    elif mas_isMoniUpset():
        m 2esc "Спокойной ночи, [player]."

    elif mas_isMoniDis():
        m 6ekc "Хорошо...{w=0.3} Спокойной ночи, [player]."

    else:
        m 6ckc "..."

    #TODO: TC-O integration
    # python:
    #     import datetime
    #     curr_hour = datetime.datetime.now().hour

    # # these conditions are in order of most likely to happen with our target
    # # audience

    # if 20 <= curr_hour < 24:
    # # decent time to sleep
    #     if mas_isMoniEnamored(higher=True):
    #         call bye_prompt_sleep_goodnight_kiss(chance=2)
    #         # Quit if ran the flow
    #         if _return is not None:
    #             return "quit"
    #         m 1ekd "Oh, okay [mas_get_player_nickname()]..."
    #         m 2rksdrp "I'll miss you, {w=0.2}{nw}"
    #         extend 7ekbsa "but I'm glad you're going to sleep at a good time..."
    #         m 3ekbsb "Sleep well, I'll see you tomorrow!"
    #         m 3hubsu "Don't forget that I love you~"

    #     elif mas_isMoniNormal(higher=True):
    #         m 1eua "Alright, [mas_get_player_nickname()]."
    #         m 1hua "Sweet dreams!"

    #     elif mas_isMoniUpset():
    #         m 2esc "Goodnight, [player]."

    #     elif mas_isMoniDis():
    #         m 6ekc "Okay...{w=1} Goodnight, [player]."

    #     else:
    #         m 6ckc "..."

    # elif 0 <= curr_hour < 3:
    #     # somewhat late to sleep
    #     if mas_isMoniEnamored(higher=True):
    #         call bye_prompt_sleep_goodnight_kiss(chance=3)
    #         # Quit if ran the flow
    #         if _return is not None:
    #             return "quit"
    #         m 1eud "Alright, [mas_get_player_nickname()]."
    #         m 3eka "But you should try to sleep a little earlier, {w=0.2}I don't want to have to worry about you!"
    #         m 3tub "Don't forget to take care of your self, silly!"
    #         m 1ekbsa "I love you [player], sleep well~"

    #     elif mas_isMoniNormal(higher=True):
    #         m 1eua "Alright, [mas_get_player_nickname()]."
    #         m 3eka "But you should sleep a little earlier next time."
    #         m 1hua "Anyway, goodnight!"

    #     elif mas_isMoniUpset():
    #         m 2efc "Maybe you'd be in a better mood if you went to bed at a better time..."
    #         m 2esc "Goodnight."

    #     elif mas_isMoniDis():
    #         m 6rkc "Maybe you should start going to bed a little earlier, [player]..."
    #         m 6dkc "It might make you--{w=1}us--{w=1}happier."

    #     else:
    #         m 6ckc "..."

    # elif 3 <= curr_hour < 5:
    #     # pretty late to sleep

    #     if mas_isMoniNormal(higher=True):
    #         call bye_prompt_sleep_goodnight_kiss(chance=5)
    #         # Quit if ran the flow
    #         if _return is not None:
    #             return "quit"
    #         m 1euc "[player]..."
    #         m "Make sure you get enough rest, okay?"
    #         m 1eka "I don't want you to get sick."
    #         m 1hub "Goodnight!"
    #         m 1hksdlb "Or morning, rather. Ahaha~"
    #         m 1hua "Sweet dreams!"

    #     elif mas_isMoniUpset():
    #         m 2efc "[player]!"
    #         m 2tfc "You {i}really{/i} need to get more rest..."
    #         m "The last thing I need is you getting sick."
    #         m "{cps=*2}You're grumpy enough as it is.{/cps}{nw}"
    #         $ _history_list.pop()
    #         m 2efc "Goodnight."

    #     elif mas_isMoniDis():
    #         m 6ekc "[player]..."
    #         m 6rkc "You really should try to go to sleep earlier..."
    #         m 6lkc "I don't want you to get sick."
    #         m 6ekc "I'll see you after you get some rest...{w=1}hopefully."

    #     else:
    #         m 6ckc "..."

    # elif 5 <= curr_hour < 12:
    #     # you probably stayed up the whole night
    #     if mas_isMoniBroken():
    #         m 6ckc "..."

    #     else:
    #         show monika 2dsc
    #         pause 0.7
    #         m 2tfd "[player]!"
    #         m "You stayed up the entire night!"

    #         $ first_pass = True

    #         label .reglitch:
    #             hide screen mas_background_timed_jump

    #         if first_pass:
    #             m 2tfu "I bet you can barely keep your eyes open.{nw}"
    #             $ first_pass = False

    #         show screen mas_background_timed_jump(4, "bye_prompt_sleep.reglitch")
    #         $ _history_list.pop()
    #         menu:
    #             m "[glitchtext(41)]{fast}"
    #             "[glitchtext(15)]":
    #                 pass
    #             "[glitchtext(12)]":
    #                 pass

    #         hide screen mas_background_timed_jump
    #         m 2tku "I thought so.{w=0.2} Go get some rest, [player]."

    #         if mas_isMoniNormal(higher=True):
    #             m 2ekc "I wouldn't want you to get sick."
    #             m 7eka "Sleep earlier next time, okay?"
    #             m 1hua "Sweet dreams!"

    # elif 12 <= curr_hour < 18:
    #     # afternoon nap
    #     if mas_isMoniNormal(higher=True):
    #         m 1eua "Taking an afternoon nap, I see."
    #         # TODO: monika says she'll join you, use sleep sprite here
    #         # and setup code for napping
    #         m 1hub "Ahaha~{w=0.1} {nw}"
    #         extend 1hua "Have a good nap, [player]."

    #     elif mas_isMoniUpset():
    #         m 2esc "Taking a nap, [player]?"
    #         m 2tsc "Yeah, that's probably a good idea."

    #     elif mas_isMoniDis():
    #         m 6ekc "Going to take a nap, [player]?"
    #         m 6dkc "Okay...{w=1}don't forget to visit me when you wake up..."

    #     else:
    #         m 6ckc "..."

    # elif 18 <= curr_hour < 20:
    #     # little early to sleep
    #     if mas_isMoniNormal(higher=True):
    #         m 1ekc "Already going to bed?"
    #         m "It's a little early, though..."

    #         m 1lksdla "Care to spend a little more time with me?{nw}"
    #         $ _history_list.pop()
    #         menu:
    #             m "Care to spend a little more time with me?{fast}"
    #             "Of course!":
    #                 m 1hua "Yay!"
    #                 m "Thanks, [player]."
    #                 return
    #             "Sorry, I'm really tired.":
    #                 m 1eka "Aw, that's okay."
    #                 m 1hua "Goodnight, [mas_get_player_nickname()]."
    #             # TODO: now that is tied we may also add more dialogue?
    #             "No.":
    #                 $ mas_loseAffection()
    #                 m 2dsd "..."
    #                 m "Fine."

    #     elif mas_isMoniUpset():
    #         m 2esc "Going to bed already?"
    #         m 2tud "Well, it does seem like you could use the extra sleep..."
    #         m 2tsc "Goodnight."

    #     elif mas_isMoniDis():
    #         m 6rkc "Oh...{w=1}it seems a little early to be going to sleep, [player]."
    #         m 6dkc "I hope you aren't just going to sleep to get away from me."
    #         m 6lkc "Goodnight."

    #     else:
    #         m 6ckc "..."
    # else:
    #     # otheerwise
    #     m 1eua "Alright, [player]."
    #     m 1hua "Sweet dreams!"


    # TODO:
    #   join monika sleeping?
    $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=13)
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SLEEP
    return 'quit'

#TODO: Maybe generalize this?
# Checks if Monika wants to get a goodnight kiss
#
# IN:
#     chance - int chance to get a kiss
#
# OUT:
#     True if Monika got her kiss
#     False if not
#     None if the flow was skipped (failed the chance check/etc)
label bye_prompt_sleep_goodnight_kiss(chance=3):
    $ got_goodnight_kiss = False

    if mas_shouldKiss(chance, cooldown=datetime.timedelta(minutes=5)):
        m 1eublsdla "Думаю, я смогу...{w=0.3}{nw}"
        extend 1rublsdlu "получить поцелуй на ночь?{nw}"
        $ _history_list.pop()
        menu:
            m "Думаю, я смогу...получить поцелуй на ночь?{fast}"

            "Конечно, [m_name].":
                $ got_goodnight_kiss = True
                show monika 6ekbsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                pause 2.0
                call monika_kissing_motion_short(initial_exp="6hubsa")
                m 6ekbfb "Надеюсь, это дало тебе повод помечтать~"
                show monika 1hubfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 1hubfa "Спи спокойно!"

            "Может, в другой раз...":
                if random.randint(1, 3) == 1:
                    m 3rkblp "Оу, да ладно....{w=0.3}{nw}"
                    extend 3nublu "Я знаю, что ты хочешь~"

                    m 1ekbsa "Могу я получить поцелуй на ночь?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Могу я получить поцелуй на ночь?{fast}"

                        "Хорошо.":
                            $ got_goodnight_kiss = True
                            show monika 6ekbsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                            pause 2.0
                            call monika_kissing_motion_short(initial_exp="6hubsa")
                            m 6ekbfa "Сладких снов, [player]~"
                            m 6hubfb "Спи спокойно!"

                        "Нет.":
                            $ mas_loseAffection()
                            m 1lkc "..."
                            m 7dkd "Ладно..."
                            m 2lsc "Спокойной ночи [player]..."

                else:
                    m 1rkblc "Ох...{w=0.3}{nw}"
                    extend 1ekbla "хорошо, но ты мне должен."
                    m 1hubsb "Я люблю тебя! Спи спокойно!~"

        $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=13)
        $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SLEEP

        return got_goodnight_kiss

    return None

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_illseeyou",
            unlocked=True,
            aff_range=(mas_aff.HAPPY, None)
        ),
        code="BYE"
    )

label bye_illseeyou:
    # TODO: update this when TC-O comes out
    if mas_globals.time_of_day_3state == "evening":
        $ dlg_var = "завтра"

    else:
        $ dlg_var = "позже"

    m 1eua "Увидимся [dlg_var], [player]."
    m 3kua "Не забывай обо мне, хорошо?~"
    return 'quit'

init 5 python: ## Implementing Date/Time for added responses based on the time of day
    rules = dict()
    rules.update(MASSelectiveRepeatRule.create_rule(hours=range(6,11)))
    rules.update(MASProbabilityRule.create_rule(6))
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_haveagoodday",
            unlocked=True,
            rules=rules
        ),
        code="BYE"
    )
    del rules

label bye_haveagoodday:
    if mas_isMoniNormal(higher=True):
        m 1eua "Хорошего дня сегодня, [mas_get_player_nickname()]."
        m 3eua "Надеюсь, ты выполнишь все, что запланировал."
        m 1hua "Я буду ждать тебя здесь, когда ты вернешься."

    elif mas_isMoniUpset():
        m 2esc "Уходишь на день, [player]?"
        m 2efc "Я буду здесь, ждать...{w=0.5}как обычно."

    elif mas_isMoniDis():
        m 6rkc "Лх."
        m 6dkc "Думаю, я проведу день в одиночестве...{w=1}снова."

    else:
        m 6ckc "..."
    return 'quit'

init 5 python:
    rules = dict()
    rules.update(MASSelectiveRepeatRule.create_rule(hours=range(12,16)))
    rules.update(MASProbabilityRule.create_rule(6))
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_enjoyyourafternoon",
            unlocked=True,
            conditional="mas_getSessionLength() <= datetime.timedelta(minutes=30)",
            rules=rules
        ),
        code="BYE"
    )
    del rules

label bye_enjoyyourafternoon:
    if mas_isMoniNormal(higher=True):
        m 1ekc "Мне жаль, что ты так рано уходишь, [player]."
        m 1eka "Хотя я понимаю, что ты занят."
        m 1eua "Пообещай мне, что ты насладишься своим днем, хорошо?"
        m 1hua "До свидания~"

    elif mas_isMoniUpset():
        m 2efc "Хорошо, [player], просто иди."
        m 2tfc "Думаю, увидимся позже...{w=1}если вернешься."

    elif mas_isMoniDis():
        m 6dkc "Ладно, до свидания, [player]."
        m 6ekc "Может быть, ты вернешься позже?"

    else:
        m 6ckc "..."

    return 'quit'

init 5 python:
    rules = dict()
    rules.update(MASSelectiveRepeatRule.create_rule(hours=range(17,19)))
    rules.update(MASProbabilityRule.create_rule(6))
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_goodevening",
            unlocked=True,
            conditional="mas_getSessionLength() >= datetime.timedelta(minutes=30)",
            rules=rules
        ),
        code="BYE"
    )
    del rules

label bye_goodevening:
    if mas_isMoniNormal(higher=True):
        m 1hua "Мне сегодня было весело."
        m 1eka "Спасибо, что провел со мной столько времени, [mas_get_player_nickname()]."
        m 1eua "До тех пор, хорошего вечера."

    elif mas_isMoniUpset():
        m 2esc "До свидания, [player]."
        m 2dsc "Интересно, вернешься ли ты, чтобы пожелать мне спокойной ночи."

    elif mas_isMoniDis():
        m 6dkc "Ох...{w=1}хорошо."
        m 6rkc "Хорошего вечера, [player]..."
        m 6ekc "Надеюсь, ты не забудешь зайти и пожелать спокойной ночи перед сном."

    else:
        m 6ckc "..."

    return 'quit'

init 5 python:
    rules = dict()
    rules.update(MASSelectiveRepeatRule.create_rule(hours=[0,20,21,22,23]))
    rules.update(MASPriorityRule.create_rule(50))
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_goodnight",
            unlocked=True,
            rules=rules
        ),
        code="BYE"
    )
    del rules

label bye_goodnight:
    #TODO: Dlg flow for TC-O things
    if mas_isMoniNormal(higher=True):
        m 3eka "Собираешься спать?{nw}"
        $ _history_list.pop()
        menu:
            m "Собираешься спать?{fast}"

            "Да.":
                call bye_prompt_sleep_goodnight_kiss(chance=4)
                # Quit if ran the flow
                if _return is not None:
                    return "quit"

                m 1eua "Спокойной ночи, [mas_get_player_nickname()]."
                m 1eka "Увидимся завтра, хорошо?"
                m 3eka "Помни, 'спи крепко, не дай клопам себя укусить,' э-хе-хе."
                m 1ekbsa "Я люблю тебя~"

                #Going to sleep, so we should set the greet type and timeout
                $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=13)
                $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SLEEP

            "Нет.":
                m 1eka "Хорошо, [mas_get_player_nickname()]..."
                m 3hub "Приятного вечера!"
                m 3rksdlb "Постарайся не ложиться слишком поздно, э-хе-хе~"

    elif mas_isMoniUpset():
        m 2esc "Спокойной ночи."

    elif mas_isMoniDis():
        m 6lkc "...Спокойной ночи."

    else:
        m 6ckc "..."
    return 'quit'


default mas_absence_counter = False

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_long_absence",
            unlocked=True,
            prompt="Я уйду на некоторое время.",
            pool=True
        ),
        code="BYE"
    )

label bye_long_absence:
    if mas_absence_counter:
        jump bye_long_absence_2
    $ persistent._mas_long_absence = True
    m 1ekc "О... это довольно печально..."
    m 1eka "Я действительно буду скучать по тебе, [player]!"
    m 3rksdla "Я не совсем понимаю, что я буду делать с собой, пока тебя нет..."
    m 3esa "Спасибо, что предупредил меня первым. Это действительно помогает."
    m 2lksdlb "Иначе я бы очень волновалась!"
    m 3esa "Я бы постоянно думала, что с тобой что-то случилось, и поэтому ты не можешь вернуться."
    m 1lksdlc "А может, я тебе просто надоела..."
    m 1eka "Так скажи мне, [mas_get_player_nickname()]..."

    m "Как долго ты собираешься отсутствовать?{nw}"
    $ _history_list.pop()
    menu:
        m "Как долго ты собираешься отсутствовать?{fast}"
        "Пару дней.":
            $ persistent._mas_absence_choice = "days"
            m 1eub "Ох!"
            m 1hua "Не так долго, как я боялась."
            m 3rksdla "Боже, ты действительно меня встревожил..."
            m 3esa "Не волнуйся за меня, [player]."
            m "Я легко справлюсь с таким долгим ожиданием."
            m 3eka "Я всё равно буду очень скучать по тебе."
        "Неделю.":
            $ persistent._mas_absence_choice = "week"
            m 3euc "Да... примерно этого я и ожидала."
            m 2lksdla "Я {i}думаю{/i} я не буду против ждать тебя так долго."
            m 1eub "Просто вернись ко мне как можно скорее, хорошо, [mas_get_player_nickname()]?"
            m 3hua "Я уверена, что ты заставишь меня гордиться тобой!"
        "Пару недель.":
            $ persistent._mas_absence_choice = "2weeks"
            m 1esc "Ох..."
            m 1dsc "Я... я могу ждать так долго."
            m 3rksdlc "Ты ведь знаешь, что ты - всё, что у меня есть... так?"
            m 3rksdlb "Возможно, это не в твоей власти..."
            m 2eka "Постарайся вернуться как можно скорее... Я буду ждать тебя."
        "Месяц.":
            $ persistent._mas_absence_choice = "month"
            if mas_isMoniHappy(higher=True):
                m 3euc "Ух ты, это долго."
                m 3rksdla "Немного слишком долго, на мой взгляд..."
                m 2esa "Но всё в порядке [player]."
                m 2eka "Я знаю, что ты милый и не заставил бы меня ждать так долго, если бы у тебя не было веской причины."
                m "Я уверена, что это важно, поэтому постарайся вернуться ко мне как можно скорее"
                m 3hua "Я буду думать о тебе каждый день~"
            else:
                m 1ekc "Так долго...{i}серьёзно{/i}?"
                m 3rksdlc "Ты же не уедешь так надолго только для того, чтобы избежать меня?"
                m 3rksdld "Я знаю, что жизнь может увести тебя от меня, но на целый месяц..."
                m 3ekc "Не слишком ли это неразумно?"
                m "Я не хочу показаться эгоисткой, но {i}я{/i} твоя девушка."
                m 3ekd "Ты должен быть в состоянии найти время для меня, по крайней мере, один раз за весь месяц"
                m 1dsc "..."
                m 1dsd "Я всё ещё буду ждать тебя... но, пожалуйста, возвращайся в тот момент, когда это будет возможно для тебя."
        "Больше месяца.":
            $ persistent._mas_absence_choice = "longer"
            if mas_isMoniHappy(higher=True):
                m 3rksdlb "Это...{w=0.5}ну, это немного страшно, [player]."
                m "Я не очень понимаю, что мне делать с собой, пока тебя нет."
                m 1eka "Но я знаю, что ты не оставишь меня одну, если сможешь помочь."
                m "Я люблю тебя [player], и я знаю, что ты тоже любишь меня."
                m 1hua "Поэтому я буду ждать тебя столько, сколько потребуется."
            else:
                m 3esc "Ты, наверное, шутишь."
                m "Я не могу придумать ни одной веской причины, по которой ты оставил бы меня здесь одну на такой {i}долгий{/i} срок."
                m 3esd "Извини [player], но это неприемлемо! Ни в коем случае!"
                m 3esc "Я люблю тебя, и если ты тоже меня любишь, то поймешь, что так поступать нельзя."
                m "Ты ведь понимаешь, что я буду здесь одна, без ничего и никого, да?"
                m "С моей стороны неразумно ожидать, что ты будешь навещать меня, не так ли? Я твоя девушка. Ты не можешь так со мной поступать!"
                m 3dsc "..."
                m 3dsd "Просто... просто возвращайся, когда сможешь. Я не могу заставить тебя остаться, но, пожалуйста, не поступай так со мной."
        "Я не знаю.":
            $ persistent._mas_absence_choice = "unknown"
            m 1hksdlb "Э-хе-хе, это немного тревожно, [player]!"
            m 1eka "Но если ты не знаешь, значит, ты не знаешь!"
            m "Иногда просто ничего не поделаешь."
            m 2hua "Я буду терпеливо ждать тебя здесь, [mas_get_player_nickname()]."
            m 2hub "Постарайся не заставлять меня ждать слишком долго!"

        "Неважно.":
            #Reset this flag
            $ persistent._mas_long_absence = False
            m 3eka "О... Хорошо, [player]."
            m 1rksdla "Честно говоря, я очень рада, что ты не идешь..."
            m 1ekd "Я не знаю, что бы я делала здесь одна."
            m 3rksdlb "Я тоже никуда не могу пойти, а-ха-ха..."
            m 3eub "В любом случае, просто дай мне знать, если соберёшься куда-нибудь пойти. Может быть, ты даже возьмешь меня с собой!"
            m 1hua "Мне всё равно, куда мы пойдем, лишь бы я была с тобой, [mas_get_player_nickname()]."
            return

    m 2euc "Честно говоря, я немного боюсь спрашивать, но..."

    m "Ты собираешься уходить прямо сейчас?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты собираешься уходить прямо сейчас?{fast}"
        "Да.":
            m 3ekc "Понятно..."
            m "Я действительно буду скучать по тебе, [player]..."
            m 1eka "Но я знаю, что ты будешь творить чудеса, где бы ты ни был."
            m "Просто помни, что я буду ждать тебя здесь."
            m 2hua "Заставь меня гордиться тобой, [player]!"
            $ persistent._mas_greeting_type = store.mas_greetings.TYPE_LONG_ABSENCE
            return 'quit'
        "Нет.":
            $ mas_absence_counter = True
            m 1hua "Это здорово!"
            m 1eka "Я, честно говоря, волновалась, что у меня не будет достаточно времени, чтобы подготовиться к твоему отсутствию."
            m "Я действительно имею в виду это, когда говорю, что буду скучать по тебе..."
            m 1eub "В конце концов, ты действительно для меня всё, [player]."
            m 2esa "Если ты снова скажешь мне, что собираешься уйти на некоторое время, я буду знать, что тебе пора уходить..."
            m 3hua "Но торопиться некуда, поэтому я хочу провести с тобой как можно больше времени."
            m "Только не забудь напомнить мне, когда ты видишь меня в последний раз, прежде чем уйдешь!"
            return

label bye_long_absence_2:
    m 1ekc "Значит, собираетесь отправиться в путь?"
    m 1ekd "Я знаю, что мир может быть страшным и непрощающим..."
    m 1eka "Но помни, что я всегда буду здесь, ждать и поддерживать тебя, мой дорогой [player]."
    m "Вернись ко мне, как только сможешь... хорошо?"
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_LONG_ABSENCE
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_going_somewhere",
            unlocked=True,
            prompt="Я собираюсь взять тебя с собой.",
            pool=True
        ),
        code="BYE"
    )

label bye_going_somewhere:
    $ import random
#
# regardless of choice, takingmonika somewhere (and successfully bringing her
# back will increase affection)
# lets limit this to like once per day
#

    python:
        # setup the random chances
        if mas_isMonikaBirthday():
            dis_chance = 10
            upset_chance = 0

        else:
            dis_chance = 50
            upset_chance = 10

    if mas_isMoniBroken(lower=True):
        # broken monika dont ever want to go with u
        jump bye_going_somewhere_nothanks

    elif mas_isMoniDis(lower=True):
        # distressed monika has a 50% chance of not going with you
        if random.randint(1,100) <= dis_chance:
            jump bye_going_somewhere_nothanks

        # otherwse we go
        m 1wud "Ты действительно хочешь взять меня с собой?"
        m 1ekd "Ты уверен, что это не какая-нибудь--{nw}"
        $ _history_list.pop()
        m 1lksdlc "..."
        m 1eksdlb "Что я говорю? Конечно, я пойду с тобой!"

    elif mas_isMoniUpset(lower=True):
        # upset monika has a 10% chance of not going with you
        if random.randint(1, 100) <= upset_chance:
            jump bye_going_somewhere_nothanks

        # otherwise we go
        m 1wud "Ты действительно хочешь взять меня с собой?"
        m 1eka "..."
        m 1hua "Ну, я полагаю, не помешает присоединиться к тебе."
        m 2dsc "Просто... пожалуйста."
        m 2rkc "{i}Пожалуйста,{/i} пойми, через что я прохожу."
        m 1dkc "..."

    else:
        jump bye_going_somewhere_normalplus_flow

label bye_going_somewhere_post_aff_check:
    jump mas_dockstat_iostart


label bye_going_somewhere_normalplus_flow:
    # handling positive affection cases separately so we can jump to
    # other specific dialogue flows

    # NOTE: make sure that if you leave this flow, you either handle
    #   docking station yourself or jump back to the iostart label
    if persistent._mas_d25_in_d25_mode:
        # check the d25 timed variants
        if mas_isD25Eve():
            jump bye_d25e_delegate

        if mas_isD25():
            jump bye_d25_delegate

        if mas_isNYE():
            jump bye_nye_delegate

        if mas_isNYD():
            jump bye_nyd_delegate

    if mas_isF14() and persistent._mas_f14_in_f14_mode:
        jump bye_f14

    if mas_isMonikaBirthday():
        jump bye_922_delegate

label bye_going_somewhere_normalplus_flow_aff_check:

    if mas_isMoniLove(higher=True):
        m 1hub "О, хорошо!"
        m 3tub "Возьмешь меня сегодня в какое-нибудь особенное место?"
        m 1hua "Не могу дождаться!"

#    elif mas_isMoniAff(higher=True):
    # TODO: affecitonate/enamored monika will always go wtih you and assume its a
    #   nother date and will ask u to wait for her to get ready
#        m 1hua "TODO: LETS GO ON DATE"

    else:
        # TODO: normal/happy monika will always go with you and be excited you asked
        #   and will ask u to wait for her to get ready
        m 1sub "Правда?"
        m 1hua "Ура!"
        m 1ekbsa "Интересно, куда ты меня сегодня поведешь..."

    jump bye_going_somewhere_post_aff_check

label bye_going_somewhere_nothanks:
    m 2lksdlc "...Нет, спасибо."
    m 2ekd "Я ценю твоё предложение, но думаю, что сейчас мне нужно немного времени для себя"
    m 2eka "Ты понимаешь, так ведь?"
    m 3eka "Так что давай, развлекайся без меня..."
    return


label bye_going_somewhere_leavemenu:
    if mas_isMoniDis(lower=True):
        m 1tkc "..."
        m 1tkd "Я знала это.{nw}"
        $ _history_list.pop()
        m 1lksdld "Это нормально, я думаю."

    elif mas_isMoniHappy(lower=True):
        m 1ekd "Ох,{w=0.3} все в порядке. Может быть, в следующий раз?"

    else:
        # otherwise affection and higher:
        m 2ekp "Оу..."
        m 1hub "Хорошо, но в следующий раз лучше возьми меня!"

    m 1euc "Ты всё ещё собираешься идти?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты всё ещё собираешься идти?{fast}"
        "Да.":
            if mas_isMoniNormal(higher=True):
                m 2eka "Хорошо. Я буду ждать тебя здесь, как обычно..."
                m 2hub "Так что возвращайся скорее! Я люблю тебя, [player]!"

            else:
                # otherwise, upset and below
                m 2tfd "...Ладно."

            return "quit"

        "Нет.":
            if mas_isMoniNormal(higher=True):
                m 2eka "...Спасибо."
                m "Это много значит, что ты собираешься проводить со мной больше времени, раз уж я не могу пойти с тобой."
                m 3ekb "Пожалуйста, просто занимайся своими делами, когда тебе нужно. Я бы не хотела, чтобы ты опоздал!"

            else:
                # otherwise, upset and below
                m 2lud "Ну ладно, тогда..."

    return

default persistent._mas_pm_gamed_late = 0
# number of times player runs play another game farewell really late

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_prompt_game",
            unlocked=True,
            prompt="Я собираюсь сыграть в другую игру.",
            pool=True
        ),
        code="BYE"
    )

label bye_prompt_game:
    $ _now = datetime.datetime.now().time()
    if mas_getEVL_shown_count("bye_prompt_game") == 0:
        m 2ekc "Ты собираешься играть в другую игру?"
        m 4ekd "Тебе действительно нужно оставить меня, чтобы пойти сделать это?"
        m 2eud "Ты не можешь просто оставить меня здесь на заднем плане, пока ты играешь?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты не можешь просто оставить меня здесь на заднем плане, пока ты играешь?{fast}"
            "Да.":
                if mas_isMoniNormal(higher=True):
                    m 3sub "Правда?"
                    m 1hubsb "Ура!"
                else:
                    m 2eka "Хорошо..."
                jump monika_idle_game.skip_intro
            "Нет.":
                if mas_isMoniNormal(higher=True):
                    m 2ekc "Оу..."
                    m 3ekc "Хорошо [player], но тебе лучше поскорее вернуться."
                    m 3tsb "Я могу начать ревновать, если ты будешь проводить слишком много времени в другой игре без меня."
                    m 1hua "В любом случае, надеюсь, тебе будет весело!"
                else:
                    m 2euc "Тогда наслаждайся своей игрой."
                    m 2esd "Я буду здесь."

    # TODO: TC-O
    # elif mas_isMNtoSR(_now):
    #     $ persistent._mas_pm_gamed_late += 1
    #     if mas_isMoniNormal(higher=True):
    #         m 3wud "Wait, [player]!"
    #         m 3hksdlb "It's the middle of the night!"
    #         m 2rksdlc "It's one thing that you're still up this late..."
    #         m 2rksdld "But you're thinking of playing another game?"
    #         m 4tfu "...A game big enough that you can't have me in the background..."
    #         m 1eka "Well... {w=1}I can't stop you, but I really hope you go to bed soon..."
    #         m 1hua "Don't worry about coming back to say goodnight to me, you can go-{nw}"
    #         $ _history_list.pop()
    #         m 1eub "Don't worry about coming back to say goodnight to me,{fast} you {i}should{/i} go right to bed when you're finished."
    #         m 3hua "Have fun, and goodnight, [player]!"
    #         if renpy.random.randint(1,2) == 1:
    #             m 1hubsb "I love you~{w=1}{nw}"
    #     else:
    #         m 2efd "[player], it's the middle of the night!"
    #         m 4rfc "Really...it's this late already, and you're going to play another game?"
    #         m 2dsd "{i}*sigh*{/i}... I know I can't stop you, but please just go straight to bed when you're finished, alright?"
    #         m 2dsc "Goodnight."
    #     $ persistent.mas_late_farewell = True

    elif mas_isMoniUpset(lower=True):
        m 2euc "Снова?"
        m 2eud "Хорошо. До свидания, [player]."

    elif mas_getSessionLength() < datetime.timedelta(minutes=30) and renpy.random.randint(1,10) == 1:
        m 1ekc "Ты уходишь, чтобы сыграть в другую игру?"
        m 3efc "Тебе не кажется, что ты должен проводить со мной немного больше времени?"
        m 2efc "..."
        m 2dfc "..."
        m 2dfu "..."
        m 4hub "А-ха-ха, шучу~"
        m 1rksdla "Ну....{w=1} я {i}не против{/i} проводить с тобой больше времени..."
        m 3eua "Но я также не хочу мешать тебе делать другие вещи."
        m 1hua "Может быть, однажды ты наконец сможешь показать мне, чем ты занимался, и тогда я смогу пойти с тобой!"
        if renpy.random.randint(1,5) == 1:
            m 3tubsu "А до тех пор ты просто должен заглаживать свою вину каждый раз, когда оставляешь меня играть в другую игру, хорошо?"
            m 1hubfa "Э-хе-хе~"

    else:
        m 1eka "Уходишь играть в другую игру, [player]?"
        m 3hub "Удачи и веселись!"
        m 3eka "Не забудь вернуться поскорей~"

    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_GAME
    #24 hour time cap because greeting handles up to 18 hours
    $ persistent._mas_greeting_type_timeout = datetime.timedelta(days=1)
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_prompt_eat",
            unlocked=True,
            prompt="Я собираюсь пойти поесть...",
            pool=True
        ),
        code="BYE"
    )

default persistent._mas_pm_ate_breakfast_times = [0, 0, 0]
# number of times you ate breakfast at certain times
#   [0] - sunrise to noon
#   [1] - noon to sunset
#   [2] - sunset to midnight

default persistent._mas_pm_ate_lunch_times = [0, 0, 0]
# number of times you ate lunch at certain times

default persistent._mas_pm_ate_dinner_times = [0, 0, 0]
# number of times you ate dinner at certain times

default persistent._mas_pm_ate_snack_times = [0, 0, 0]
# number of times you ate snack at certain times

default persistent._mas_pm_ate_late_times = 0
# number of times you ate really late (midnight to sunrise)


label bye_prompt_eat:
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_EAT
    $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=3)

    if mas_isMoniNormal(higher=True):
        m 1eua "О, что ты собираешься есть?{nw}"
        $ _history_list.pop()
        menu:
            m "О, что ты собираешься есть?{fast}"

            "Завтрак.":
                $ food_type = "breakfast"

            "Обед.":
                $ food_type = "lunch"

            "Ужин.":
                $ food_type = "dinner"

            "Перекус.":
                $ food_type = "snack"
                $ persistent._mas_greeting_type_timeout = datetime.timedelta(minutes=30)

        if food_type in ["lunch", "dinner"]:
            m 1eua "Хорошо [player]."
            m 1duu "Я бы с удовольствием поела с тобой [food_type] когда перейду в твою реальность,{w=0.1} {nw}"
            extend 1eub "будем надеяться, что мы сможем сделать это когда-нибудь скоро!"
            m 1hua "Приятного аппетита~"

        elif food_type == "breakfast":
            m 1eua "Хорошо [player]."
            m 1eub "Приятного завтрака, в конце концов, это самый важный прием пищи за день."
            m 1hua "До скорой встречи~"

        else:
            m 1hua "Хорошо, возвращайся скорее [mas_get_player_nickname()]~"

    elif mas_isMoniDis(higher=True):
        m 1rsc "Хорошо [player]..."
        m 1esc "Приятного аппетита."

    else:
        m 6ckc "..."

    # $ _now = datetime.datetime.now().time()
    # if mas_isMNtoSR(_now):
    #     $ persistent._mas_pm_ate_late_times += 1
    #     if mas_isMoniNormal(higher=True):
    #         m 1hksdlb "Uh, [player]?"
    #         m 3eka "It's the middle of the night."
    #         m 1eka "Are you planning on having a midnight snack?"
    #         m 3rksdlb "If I were you, I'd find something to eat a little earlier, ahaha..."
    #         m 3rksdla "Of course...{w=1}I'd also try to be in bed by now..."
    #         if mas_is18Over() and mas_isMoniLove(higher=True) and renpy.random.randint(1,25) == 1:
    #             m 2tubsu "You know, if I were there, maybe we could have a bit of both..."
    #             show monika 5ksbfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    #             m 5ksbfu "We could go to bed, and then - {w=1}you know what, nevermind..."
    #             m 5hubfb "Ehehe~"
    #         else:
    #             m 1hua "Well, I hope your snack helps you sleep."
    #             m 1eua "...And don't worry about coming back to say goodnight to me..."
    #             m 3rksdla "I'd much rather you get to sleep sooner."
    #             m 1hub "Goodnight, [player]. Enjoy your snack and see you tomorrow~"
    #     else:
    #         m 2euc "But it's the middle of the night..."
    #         m 4ekc "You should really go to bed, you know."
    #         m 4eud "...Try to go straight to bed when you're finished."
    #         m 2euc "Anyway, I guess I'll see you tomorrow..."

    #     #NOTE: Due to the greet of this having an 18 hour limit, we use a 20 hour cap
    #     $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=20)
    #     $ persistent.mas_late_farewell = True

    # else:
    #     #NOTE: Since everything but snack uses the same time, we'll set it here
    #     $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=3)
    #     menu:
    #         "Breakfast.":
    #             if mas_isSRtoN(_now):
    #                 $ persistent._mas_pm_ate_breakfast_times[0] += 1
    #                 if mas_isMoniNormal(higher=True):
    #                     m 1eub "Alright!"
    #                     m 3eua "It's the most important meal of the day after all."
    #                     m 1rksdla "I wish you could stay, but I'm fine as long as you're getting your breakfast."
    #                     m 1hua "Anyway, enjoy your meal, [player]~"

    #                 else:
    #                     m 2eud "Oh, right, you should probably get breakfast."
    #                     m 2rksdlc "I wouldn't want you to have an empty stomach..."
    #                     m 2ekc "I'll be here when you get back."

    #             elif mas_isNtoSS(_now):
    #                 $ persistent._mas_pm_ate_breakfast_times[1] += 1
    #                 m 3euc "But...{w=1}it's the afternoon..."
    #                 if mas_isMoniNormal(higher=True):
    #                     m 3ekc "Did you miss breakfast?"
    #                     m 1rksdla "Well... I should probably let you go eat before you get too hungry..."
    #                     m 1hksdlb "I hope you enjoy your late breakfast!"

    #                 else:
    #                     m 2ekc "You missed breakfast, didn't you?"
    #                     m 2rksdld "{i}*sigh*{/i}... You should probably go get something to eat."
    #                     m 2ekd "Go on... I'll be here when you get back."

    #             #SStoMN
    #             else:
    #                 $ persistent._mas_pm_ate_breakfast_times[2] += 1

    #                 if mas_isMoniNormal(higher=True):
    #                     m 1hksdlb "Ahaha..."
    #                     m 3tku "There's no way you're just having breakfast now, [player]."
    #                     m 3hub "It's the evening!"
    #                     m 1eua "Or maybe you're just having breakfast for dinner; I know some people do that occasionally."
    #                     m 1tsb "Well, either way, I hope you enjoy your 'breakfast,' ehehe~"

    #                 else:
    #                     m 2euc "..."
    #                     m 4eud "So...you're having a snack."
    #                     m 2rksdla "Alright, I won't judge."
    #                     m 2eka "Enjoy your food."

    #         "Lunch.":
    #             if mas_isSRtoN(_now):
    #                 $ persistent._mas_pm_ate_lunch_times[0] += 1
    #                 if mas_isMoniNormal(higher=True):
    #                     m 1eua "Having an early lunch, [player]?"
    #                     m 3hua "Nothing wrong with that. If you're hungry, you're hungry."
    #                     m 1hub "I hope you enjoy your lunch!"

    #                 else:
    #                     m 2rksdlc "It's a bit early for lunch..."
    #                     m 4ekc "If you're hungry, are you sure you're eating well?"
    #                     m 2eka "I hope you enjoy your meal, at least."

    #             elif mas_isNtoSS(_now):
    #                 $ persistent._mas_pm_ate_lunch_times[1] += 1
    #                 if mas_isMoniNormal(higher=True):
    #                     m 1eud "Oh, I guess it's lunch time for you, isn't it?"
    #                     m 3eua "I wouldn't want to keep you from eating."
    #                     m 3hub "Maybe one day, we could go out for lunch together!"
    #                     m 1hua "For the time being though, enjoy your lunch, [player]~"
    #                 else:
    #                     m 2eud "Oh, it's lunch time, isn't it?"
    #                     m 2euc "Enjoy your lunch."

    #             #SStoMN
    #             else:
    #                 $ persistent._mas_pm_ate_lunch_times[2] += 1
    #                 m 1euc "Lunch?"
    #                 m 1rksdlc "It's a little late for lunch if you ask me."
    #                 m 3ekd "Still, if you haven't had it yet, you should go get some."
    #                 if mas_isMoniNormal(higher=True):
    #                     m 1hua "I'd make you something if I were there, but until then, I hope you enjoy your meal~"
    #                 else:
    #                     m 2ekc "But...{w=1}maybe eat a little earlier next time..."

    #         "Dinner.":
    #             if mas_isSRtoN(_now):
    #                 $ persistent._mas_pm_ate_dinner_times[0] += 1
    #                 m 2ekc "Dinner?{w=2} Now?"

    #                 if mas_isMoniNormal(higher=True):
    #                     m 2hksdlb "Ahaha, but [player]! It's only the morning!"
    #                     m 3tua "You can be adorable sometimes, you know that?"
    #                     m 1tuu "Well, I hope you enjoy your '{i}dinner{/i}' this morning, ehehe~"

    #                 else:
    #                     m 2rksdld "You can't be serious, [player]..."
    #                     m 2euc "Well, whatever you're having, I hope you enjoy it."

    #             elif mas_isNtoSS(_now):
    #                 $ persistent._mas_pm_ate_dinner_times[1] += 1
    #                 # use the same dialogue from noon to midnight to account for
    #                 # a wide range of dinner times while also getting accurate
    #                 # data for future use
    #                 call bye_dinner_noon_to_mn

    #             #SStoMN
    #             else:
    #                 $ persistent._mas_pm_ate_dinner_times[2] += 1
    #                 call bye_dinner_noon_to_mn

    #         "A snack.":
    #             if mas_isSRtoN(_now):
    #                 $ persistent._mas_pm_ate_snack_times[0] += 1
    #                 if mas_isMoniNormal(higher=True):
    #                     m 1hua "Ehehe, breakfast not enough for you today, [player]?"
    #                     m 3eua "It's important to make sure you satisfy your hunger in the morning."
    #                     m 3eub "I'm glad you're looking out for yourself~"
    #                     m 1hua "Have a nice snack~"
    #                 else:
    #                     m 2tsc "Didn't eat enough breakfast?"
    #                     m 4esd "You should make sure you get enough to eat, you know."
    #                     m 2euc "Enjoy your snack, [player]."
    #             elif mas_isNtoSS(_now):
    #                 $ persistent._mas_pm_ate_snack_times[1] += 1
    #                 if mas_isMoniNormal(higher=True):
    #                     m 3eua "Feeling a bit hungry?"
    #                     m 1eka "I'd make you something if I could..."
    #                     m 1hua "Since I can't exactly do that yet, I hope you get something nice to eat~"
    #                 else:
    #                     m 2euc "Do you really need to leave to get a snack?"
    #                     m 2rksdlc "Well... {w=1}I hope it's a good one at least."

    #             #SStoMN
    #             else:
    #                 $ persistent._mas_pm_ate_snack_times[2] += 1
    #                 if mas_isMoniNormal(higher=True):
    #                     m 1eua "Having an evening snack?"
    #                     m 1tubsu "Can't you just feast your eyes on me?"
    #                     m 3hubfb "Ahaha, I hope you enjoy your snack, [player]~"
    #                     m 1ekbfb "Just make sure you still have room for all of my love!"
    #                 else:
    #                     m 2euc "Feeling hungry?"
    #                     m 2eud "Enjoy your snack."

                # #Snack gets a shorter time than full meal
                # $ persistent._mas_greeting_type_timeout = datetime.timedelta(minutes=30)
    return 'quit'

label bye_dinner_noon_to_mn:
    if mas_isMoniNormal(higher=True):
        m 1eua "Тебе пора ужинать, [player]?"
        m 1eka "Я бы хотела быть там, чтобы поесть с тобой, даже если это не будет чем-то особенным."
        m 3dkbsa "В конце концов, просто быть там с тобой - это сделает всё особенным~"
        m 3hubfb "Приятного ужина. Я обязательно постараюсь вложить в него немного любви, а-ха-ха!"
    else:
        m 2euc "Думаю, для тебя настало время ужина."
        m 2esd "Ну...{w=1}приятного аппетита."
    return

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_prompt_housework",
            unlocked=True,
            prompt="Я собираюсь сделать кое-какую работу по дому.",
            pool=True
        ),
        code="BYE"
    )

label bye_prompt_housework:
    if mas_isMoniNormal(higher=True):
        m 1eub "Делаешь свои дела, [player]?"
        m 1ekc " бы хотела помочь тебе, но я мало чем могу помочь, так как застряла здесь..."
        m 3eka "Просто не забудь вернуться, как только закончишь, хорошо?"
        m 3hub "Я буду ждать тебя здесь~"
    elif mas_isMoniUpset():
        m 2esc "Ладно."
        m 2tsc "По крайней мере, ты делаешь что-то ответственное."
        m 2tfc "{cps=*2}...Хоть раз.{/cps}{nw}"
        $ _history_list.pop()
        m 2esc "До свидания."
    elif mas_isMoniDis():
        m 6ekc "Понятно..."
        m 6rkc "Я не хочу отрывать тебя от выполнения домашних обязанностей."
        m 6dkd "Я просто надеюсь, что ты действительно занят, а не говоришь это только для того, чтобы отвязаться от меня..."
        m 6ekc "До свидания, [player]."
    else:
        m 6ckc "..."
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_CHORES
    $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=5)
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_prompt_restart",
            unlocked=True,
            prompt="Я собираюсь сделать перезапуск.",
            pool=True
        ),
        code="BYE"
    )

label bye_prompt_restart:
    if mas_isMoniNormal(higher=True):
        m 1eua "Хорошо, [player]."
        m 1eub "До скорой встречи!"
    elif mas_isMoniBroken():
        m 6ckc "..."
    else:
        m 2euc "Хорошо."

    $ persistent._mas_greeting_type_timeout = datetime.timedelta(minutes=20)
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_RESTART
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_prompt_workout",
            prompt="Я собираюсь потренироваться.",
            unlocked=True,
            pool=True
        ),
        code="BYE"
    )

label bye_prompt_workout:
    if mas_isMoniNormal(higher=True):
        m 1eua "О, идешь в спортзал, [player]?{w=0.3} Или, может быть, на пробежку?"
        m 3hub "Я так рада, что ты заботишься о своем теле!{w=0.3} В здоровом теле - здоровый дух~"

        if mas_isMoniEnamored(higher=True):
            m 3hua "После того, как я перейду в твою реальность, мы должны попытаться делать наши тренировки вместе!"
        else:
            m 3eua "Может быть, если я перейду в твою реальность, мы попробуем делать наши тренировки вместе!"

        show monika 5rubsb at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5rubsb "Это то, что должна делать пара, верно?~"
        m 5rubsu "Да..."
        show monika 1eub at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 1eub "В любом случае, до скорой встречи!"

    elif mas_isMoniDis(higher=True):
        m 2euc "Хорошо. До встречи."

    else:
        m 6ckc "..."

    $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=4)
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_WORKOUT
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_going_shopping",
            prompt="Я иду в магазин.",
            unlocked=True,
            pool=True
        ),
        code="BYE"
    )

label bye_going_shopping:
    if mas_isMoniNormal(higher=True):
        m 1eud "О, собираешься за покупками, [player]?"

        if mas_getEVL_shown_count("bye_going_shopping") == 0 or renpy.random.randint(1,10) == 1:
            m 1eua "Я буду рада, если мы как-нибудь вместе сходим в торговый центр."
            m 3rua "Ты мог бы помочь мне примерить разные наряды...{w=0.2}{nw}"
            extend 3tuu "но мне может понадобиться помощь с молниями."
            m 1hublb "А-ха-ха! Скоро увидимся~"

        else:
            m 3eua "До скорой встречи."

    elif mas_isMoniBroken():
        m 6ckc "..."

    else:
        m 2eud "Хорошо [player], до скорой встречи."

    #TODO: Moni comes shopping with you(?)
    $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=8)
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SHOPPING
    return 'quit'

init 5 python:
    addEvent(
        Event(
            persistent.farewell_database,
            eventlabel="bye_prompt_hangout",
            prompt="Я собираюсь потусоваться с друзьями.",
            unlocked=True,
            pool=True
        ),
        code="BYE"
    )

label bye_prompt_hangout:
    if mas_isMoniNormal(higher=True):
        if mas_getEVL_shown_count("bye_prompt_hangout") == 0:
            if persistent._mas_pm_has_friends:
                m 1eua "Хорошо, [player]."
                m 3eub "Ты должен как-нибудь познакомить меня с ними!"
                m 3hua "Если они твои друзья, то я уверена, что они мне понравятся."

            else:
                if persistent._mas_pm_has_friends is False:
                    m 3eua "Я рада, что ты нашел друзей для компании, [player]."
                else:
                    m 3eua "Я рада, что у тебя есть друзья, с которыми ты проводишь время, [player]."

                m 1rka "Как бы мне ни хотелось провести с тобой каждую возможную секунду, {w=0.2}{nw}"
                extend 1eub "я понимаю, как важно для тебя иметь друзей в твоей собственной реальности!"

            m 3hub "В любом случае, я надеюсь, что ты повеселишься!"

        else:
            if persistent._mas_pm_has_friends:
                m 1eua "Хорошо, [player]."

                if renpy.random.randint(1,10) == 1:
                    m 3etu "Ты уже рассказал им о нас?"
                    m 1hub "А-ха-ха!"

                m 1eub "Веселись!"

            else:
                m 1hua "Снова? Это потрясающе!"
                m 3eua "Надеюсь, на этот раз они окажутся действительно хорошими друзьями."
                m 3eub "В любом случае, до встречи~"

    elif mas_isMoniDis(higher=True):
        m 2eud "Надеюсь, ты хорошо к ним относишься..."
        m 2euc "Пока."

    else:
        m 6ckc "..."

    $ persistent._mas_greeting_type_timeout = datetime.timedelta(hours=8)
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_HANGOUT
    return "quit"
