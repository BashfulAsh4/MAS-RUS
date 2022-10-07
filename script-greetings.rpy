##This page holds all of the random greetings that Monika can give you after you've gone through all of her "reload" scripts

#Make a list of every label that starts with "greeting_", and use that for random greetings during startup

# HOW GREETINGS USE EVENTS:
#   unlocked - determines if the greeting can even be shown
#   rules - specific event rules are used for things:
#       MASSelectiveRepeatRule - repeat on certain year/month/day/whatever
#       MASNumericalRepeatRule - repeat every x time
#       MASPriorityRule - priority of this event. if not given, we assume
#           the default priority (which is also the lowest)

# PRIORITY RULES:
#   Special, moni wants/debug greetings should have negative priority.
#   special event greetings should have priority 10-50
#   non-special event, but somewhat special compared to regular greets should
#       be 50-100
#   random/everyday greetings should be 100 or larger. The default prority
#   will be 500

# persistents that greetings use
default persistent._mas_you_chr = False

# persistent containing the greeting type
# that should be selected None means default
default persistent._mas_greeting_type = None

# cutoff for a greeting type.
# if timedelta, then we add this time to last session end to check if the
#   type should be cleared
# if datetime, then we compare it to the current dt to check if type should be
#   cleared
default persistent._mas_greeting_type_timeout = None

default persistent._mas_idle_mode_was_crashed = None
# this gets to set to True if the user crashed during idle mode
# or False if the user quit during idle mode.
# in your idle greetings, you can assume that it will NEVER be None

init -1 python in mas_greetings:
    import store
    import store.mas_ev_data_ver as mas_edv
    import datetime
    import random

    # TYPES:
    TYPE_SCHOOL = "school"
    TYPE_WORK = "work"
    TYPE_SLEEP = "sleep"
    TYPE_LONG_ABSENCE = "long_absence"
    TYPE_SICK = "sick"
    TYPE_GAME = "game"
    TYPE_EAT = "eat"
    TYPE_CHORES = "chores"
    TYPE_RESTART = "restart"
    TYPE_SHOPPING = "shopping"
    TYPE_WORKOUT = "workout"
    TYPE_HANGOUT = "hangout"

    ### NOTE: all Return Home greetings must have this
    TYPE_GO_SOMEWHERE = "go_somewhere"

    # generic return home (this also includes bday)
    TYPE_GENERIC_RET = "generic_go_somewhere"

    # holiday specific
    TYPE_HOL_O31 = "o31"
    TYPE_HOL_O31_TT = "trick_or_treat"
    TYPE_HOL_D25 = "d25"
    TYPE_HOL_D25_EVE = "d25e"
    TYPE_HOL_NYE = "nye"
    TYPE_HOL_NYE_FW = "fireworks"

    # crashed only
    TYPE_CRASHED = "generic_crash"

    # reload dialogue only
    TYPE_RELOAD = "reload_dlg"

    # High priority types
    # These types ALWAYS override greeting priority rules
    # These CANNOT be override with GreetingTypeRules
    HP_TYPES = [
        TYPE_GO_SOMEWHERE,
        TYPE_GENERIC_RET,
        TYPE_LONG_ABSENCE,
        TYPE_HOL_O31_TT
    ]

    NTO_TYPES = (
        TYPE_GO_SOMEWHERE,
        TYPE_GENERIC_RET,
        TYPE_LONG_ABSENCE,
        TYPE_CRASHED,
        TYPE_RELOAD,
    )

    # idle mode returns
    # these are meant if you had a game crash/quit during idle mode


    def _filterGreeting(
            ev,
            curr_pri,
            aff,
            check_time,
            gre_type=None
        ):
        """
        Filters a greeting for the given type, among other things.

        IN:
            ev - ev to filter
            curr_pri - current loweset priority to compare to
            aff - affection to use in aff_range comparisons
            check_time - datetime to check against timed rules
            gre_type - type of greeting we want. We just do a basic
                in check for category. We no longer do combinations
                (Default: None)

        RETURNS:
            True if this ev passes the filter, False otherwise
        """
        # NOTE: new rules:
        #   eval in this order:
        #   1. hidden via bitmask
        #   2. priority (lower or same is True)
        #   3. type/non-0type
        #   4. unlocked
        #   5. aff_ramnge
        #   6. all rules
        #   7. conditional
        #       NOTE: this is never cleared. Please limit use of this
        #           property as we should aim to use lock/unlock as primary way
        #           to enable or disable greetings.

        # check if hidden from random select
        if ev.anyflags(store.EV_FLAG_HFRS):
            return False

        # priority check, required
        # NOTE: all greetings MUST have a priority
        if store.MASPriorityRule.get_priority(ev) > curr_pri:
            return False

        # type check, optional
        if gre_type is not None:
            # with a type, we may have to match the type

            if gre_type in HP_TYPES:
                # this type is a high priority type and MUST be matched.

                if ev.category is None or gre_type not in ev.category:
                    # must have a matching type
                    return False

            elif ev.category is not None:
                # greeting has types

                if gre_type not in ev.category:
                # but does not have the current type
                    return False

            elif not store.MASGreetingRule.should_override_type(ev):
                # greeting does not have types, but the type is not high
                # priority so if the greeting doesnt alllow
                # type override then it cannot be used
                return False

        elif ev.category is not None:
            # without type, ev CANNOT have a type
            return False

        # unlocked check, required
        if not ev.unlocked:
            return False

        # aff range check, required
        if not ev.checkAffection(aff):
            return False

        # rule checks
        if not (
            store.MASSelectiveRepeatRule.evaluate_rule(
                check_time, ev, defval=True)
            and store.MASNumericalRepeatRule.evaluate_rule(
                check_time, ev, defval=True)
            and store.MASGreetingRule.evaluate_rule(ev, defval=True)
            and store.MASTimedeltaRepeatRule.evaluate_rule(ev)
        ):
            return False

        # conditional check
        if not ev.checkConditional():
            return False

        # otherwise, we passed all tests
        return True


    # custom greeting functions
    def selectGreeting(gre_type=None, check_time=None):
        """
        Selects a greeting to be used. This evaluates rules and stuff
        appropriately.

        IN:
            gre_type - greeting type to use
                (Default: None)
            check_time - time to use when doing date checks
                If None, we use current datetime
                (Default: None)

        RETURNS:
            a single greeting (as an Event) that we want to use
        """
        if (
                store.persistent._mas_forcegreeting is not None
                and renpy.has_label(store.persistent._mas_forcegreeting)
            ):
            return store.mas_getEV(store.persistent._mas_forcegreeting)

        # local reference of the gre database
        gre_db = store.evhand.greeting_database

        # setup some initial values
        gre_pool = []
        curr_priority = 1000
        aff = store.mas_curr_affection

        if check_time is None:
            check_time = datetime.datetime.now()

        # now filter
        for ev_label, ev in gre_db.iteritems():
            if _filterGreeting(
                    ev,
                    curr_priority,
                    aff,
                    check_time,
                    gre_type
                ):

                # change priority levels and stuff if needed
                ev_priority = store.MASPriorityRule.get_priority(ev)
                if ev_priority < curr_priority:
                    curr_priority = ev_priority
                    gre_pool = []

                # add to pool
                gre_pool.append(ev)

        # not having a greeting to show means no greeting.
        if len(gre_pool) == 0:
            return None

        return random.choice(gre_pool)


    def checkTimeout(gre_type):
        """
        Checks if we should clear the current greeting type because of a
        timeout.

        IN:
            gre_type - greeting type we are checking

        RETURNS: passed in gre_type, or None if timeout occured.
        """
        tout = store.persistent._mas_greeting_type_timeout

        # always clear the timeout
        store.persistent._mas_greeting_type_timeout = None

        if gre_type is None or gre_type in NTO_TYPES or tout is None:
            return gre_type

        if mas_edv._verify_td(tout, False):
            # this is a timedelta, compare with last session end
            last_sesh_end = store.mas_getLastSeshEnd()
            if datetime.datetime.now() < (tout + last_sesh_end):
                # havent timedout yet
                return gre_type

            # otherwise has timed out
            return None

        elif mas_edv._verify_dt(tout, False):
            # this is a datetime, compare with current dt
            if datetime.datetime.now() < tout:
                # havent timedout yet
                return gre_type

            # otherwise has timeed out
            return None

        return gre_type


# NOTE: this is auto pushed to be shown after an idle mode greeting
label mas_idle_mode_greeting_cleanup:
    $ mas_resetIdleMode()
    return


init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_sweetheart",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_sweetheart:
    m 1hub "И снова здравствуй, милый!"

    if persistent._mas_player_nicknames:
        m 1eka "Как приятно видеть тебя снова."
        m 1eua "Что будем делать этим [mas_globals.time_of_day_3state], [player]?"

    else:
        m 1lkbsa "Как-то неловко говорить об этом вслух, не так ли?"
        m 3ekbfa "Тем не менее, я думаю, что это нормально - смущаться время от времени."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_honey",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_honey:
    m 1hub "С возвращением, дорогой!"
    m 1eua "Я так рада видеть тебя снова."
    m "Давай проведем ещё немного времени вместе, хорошо?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=12)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None)
        ),
        code="GRE"
    )

label greeting_back:
    $ tod = "день" if mas_globals.time_of_day_4state != "вечер" else "ночь"
    m 1eua "[player], ты вернулся!"
    m 1eka "Я уже начала скучать по тебе."
    m 1hua "Давай проведем еще один прекрасный [tod] вместе, хорошо?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_gooday",
            unlocked=True,
        ),
        code="GRE"
    )

label greeting_gooday:
    if mas_isMoniNormal(higher=True):
        m 1hua "Снова здравствуй, [player]. Как дела?"

        m "У тебя сегодня был хороший день?{nw}"
        $ _history_list.pop()
        menu:
            m "У тебя сегодня был хороший день?{fast}"
            "Да.":
                m 1hub "Я очень рада, [player]."
                m 1eua "Я чувствую себя намного лучше, зная, что ты счастлив."
                m "Я постараюсь сделать все возможное, чтобы так было и впредь, обещаю"
            "Нет...":
                m 1ekc "Ох..."
                m 2eka "Ну, не волнуйся, [player]. Я всегда рядом с тобой."
                m "Мы можем весь день говорить о твоих проблемах, если ты хочешь."
                m 3eua "Я хочу постараться сделать так, чтобы ты всегда был счастлив."
                m 1eka "Потому что это то, что делает меня счастливой."
                m 1hua "Я обязательно постараюсь сделать всё возможное, чтобы поднять тебе настроение, обещаю."

    elif mas_isMoniUpset():
        m 2esc "[player]."

        m "Как проходит твой день?{nw}"
        $ _history_list.pop()
        menu:
            m "Как проходит твой день?{fast}"
            "Хорошо.":
                m 2esc "{cps=*2}Должно быть хорошо.{/cps}{nw}"
                $ _history_list.pop()
                m "Это хорошо..."
                m 2dsc "По крайней мере, у {i}кого-то{/i} хороший день."

            "Плохо.":
                m "Ох..."
                m 2efc "{cps=*2}Это должно пойти хорошо..{/cps}{nw}"
                $ _history_list.pop()
                m 2dsc "Ну, я-то уж точно знаю, что {i}это{/i} такое."

    elif mas_isMoniDis():
        m 6ekc "Ох...{w=1} Привет, [player]."

        m "К-как проходит твой день?{nw}"
        $ _history_list.pop()
        menu:
            m "К-как проходит твой день?{fast}"
            "Хорошо.":
                m 6dkc "Это...{w=1}хорошо."
                m 6rkc "Надеюсь, так и останется."
            "Плохо.":
                m 6rkc "Я-я поняла."
                m 6dkc "В последнее время у меня тоже было много таких дней..."

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit:
    m 1eua "А вот и ты [player], очень приятно, что ты навестил меня."
    m 1eka "Ты всегда такой заботливый."
    m 1hua "Спасибо, что проводишь со мной так много времени~"
    return

# TODO this one no longer needs to do all that checking, might need to be broken
# in like 3 labels though
# TODO: just noting that this should be worked on at some point.
# TODO: new greeting rules can enable this, but we will do it later

label greeting_goodmorning:
    $ current_time = datetime.datetime.now().time().hour
    if current_time >= 0 and current_time < 6:
        m 1hua "Доброе утро--"
        m 1hksdlb "--ох, подожди."
        m "Сейчас глубокая ночь, дорогой."
        m 1euc "Что ты делаешь, проснувшись в такое время?"
        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eua "Полагаю, ты не можешь заснуть..."

        m "Это так?{nw}"
        $ _history_list.pop()
        menu:
            m "Это так?{fast}"
            "Да.":
                m 5lkc "Тебе действительно нужно поспать, если можешь."
                show monika 3euc at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 3euc "Засиживаться допоздна вредно для здоровья, понимаешь?"
                m 1lksdla "Но если это означает, что я буду видеть тебя чаще, я не могу жаловаться."
                m 3hksdlb "А-ха-ха!"
                m 2ekc "Но всё же..."
                m "Я бы не хотела, чтобы ты так с собой поступал."
                m 2eka "Сделай перерыв, если тебе нужно, хорошо? Сделай это ради меня."
            "Нет.":
                m 5hub "Ах. Тогда я чувствую облегчение."
                m 5eua "Значит ли это, что ты здесь только ради меня, посреди ночи?"
                show monika 2lkbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 2lkbsa "Боже, я так счастлива!"
                m 2ekbfa "Ты действительно заботишься обо мне [player]."
                m 3tkc "Но если ты действительно устал, пожалуйста, иди спать!"
                m 2eka "Я очень люблю тебя, поэтому не утомляйся!"
    elif current_time >= 6 and current_time < 12:
        m 1hua "Доброе утро, дорогой."
        m 1esa "Ещё одно свежее утро, чтобы начать день, да?"
        m 1eua "Я рада, что вижу тебя этим утром~"
        m 1eka "Не забывай заботиться о себе, хорошо?"
        m 1hub "Заставь меня гордиться тобой сегодня, как всегда!"
    elif current_time >= 12 and current_time < 18:
        m 1hua "Добрый день, [mas_get_player_nickname()]."
        m 1eka "Не позволяй стрессу взять над тобой верх, хорошо?"
        m "Я знаю, что сегодня ты снова будешь стараться изо всех сил, но..."
        m 4eua "Все равно важно сохранять ясный ум!"
        m "Следи за своим самочувствием, делай глубокие вдохи..."
        m 1eka "Я обещаю, что не буду жаловаться, если ты выйдешь из игры, так что делай то, что должен."
        m "Или ты можешь остаться со мной, если хочешь."
        m 4hub "Просто помни, я люблю тебя!"
    elif current_time >= 18:
        m 1hua "Добрый вечер, любимый!"

        m "У тебя сегодня был хороший день?{nw}"
        $ _history_list.pop()
        menu:
            m "У тебя сегодня был хороший день?{fast}"
            "Да.":
                m 1eka "Ах, как хорошо!"
                m 1eua "Я не могу не чувствовать себя счастливой, когда ты счастлив..."
                m "Но это же хорошо, правда?"
                m 1ekbsa "Я так люблю тебя, [player]."
                m 1hubfb "А-ха-ха!"
            "Нет.":
                m 1tkc "О боже..."
                m 1eka "Надеюсь, скоро тебе станет лучше, хорошо?"
                m "Просто помни, что бы ни случилось, что бы кто ни сказал или ни сделал..."
                m 1ekbsa "Я люблю тебя очень, очень сильно"
                m "Просто оставайся со мной, если тебе от этого станет легче."
                m 1hubfa "Я люблю тебя, [player], правда люблю."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back2",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=20)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_back2:
    m 1eua "Здравствуй, дорогой."
    m 1ekbsa "Я начала ужасно скучать по тебе. Я так рада снова тебя видеть!"
    m 1hubfa "Не заставляй меня ждать так долго в следующий раз, э-хе-хе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back3",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(days=1)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_back3:
    m 1eka "Я так скучала по тебе, [player]!"
    m "Спасибо, что вернулся. Мне действительно нравится проводить с тобой время."
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 2wfx"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back4",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=10)",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_back4:
    m 2wfx "Эй, [player]!"
    m "Тебе не кажется, что ты заставил меня ждать слишком долго?"
    m 2hfu "..."
    m 2hub "А-ха-ха!"
    m 2eka "Я просто шучу. Я никогда не смогу злиться на тебя."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit2",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit2:
    m 1hua "Спасибо, что проводишь со мной так много времени, [player]."
    m 1eka "Каждая минута, проведенная с тобой, подобна пребыванию в раю!"
    m 1lksdla "Надеюсь, это прозвучало не слишком глупо, э-хе-хе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit3",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=15)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit3:
    m 1hua "Ты вернулся!"
    m 1eua "Я уже начала скучать по тебе..."
    m 1eka "Не заставляй меня ждать так долго в следующий раз, хорошо?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back5",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=15)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_back5:
    m 1hua "Я так рада снова тебя видеть!"
    m 1eka "Я уже начала волноваться за тебя."
    m "Пожалуйста, не забывай приходить ко мне, хорошо? Я всегда буду ждать тебя здесь."
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit4",
            conditional="store.mas_getAbsenceLength() <= datetime.timedelta(hours=3)",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_visit4:
    if mas_getAbsenceLength() <= datetime.timedelta(minutes=30):
        m 1wud "О! [player]!"
        m 3sub "Ты вернулся!"
        m 3hua "Я так счастлива, что ты вернулся и навестил меня так скоро~"
    else:
        m 1hub "Я люююблю тееебя, [player]. Э-хе-хе~"
        m 1hksdlb "Ох, прости! Я просто отвлеклась."
        m 1lksdla "Я не думала, что смогу увидеть тебя снова так скоро."
        $ mas_ILY()
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 5hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit5",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_visit5:
    m 5hua "{i}~Каждый день,~\n~я представляю будущее, где я могу быть с тобой...~{/i}"
    m 5wuw "О, ты здесь! Я просто мечтала и немного пела."
    show monika 1lsbssdrb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 1lsbssdrb "Думаю, нетрудно догадаться, о чём я мечтала, а-ха-ха~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit6",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit6:
    m 1hua "Каждый день становится всё лучше и лучше, когда ты рядом со мной!"
    m 1eua "При этом я так счастлива, что ты наконец-то здесь."
    m "Давай проведем еще один замечательный [mas_globals.time_of_day_3state] вместе."
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1gsu"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back6",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_back6:
    m 3tku "Эй, [player]!"
    m "Тебе действительно стоит навещать меня почаще."
    m 2tfu "Ты знаешь, что случается с людьми, которые мне не нравятся, в конце концов..."
    m 1hksdrb "Я просто дразню тебя, э-хе-хе~"
    m 1hua "Не будь таким доверчивым! Я никогда не причиню тебе вреда."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit7",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit7:
    m 1hub "Ты здесь, [player]!"
    m 1eua "Готов ли ты провести ещё немного времени вместе? Э-хе-хе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit8",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit8:
    m 1hub "Я так рада, что ты здесь, [player]!"
    m 1eua "Что мы должны сделать сегодня?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit9",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=1)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit9:
    m 1hua "Наконец-то ты вернулся! Я ждала тебя."
    m 1hub "Ты готов провести со мной немного времени? Э-хе-хе~"
    return

#TODO needs additional dialogue so can be used for all aff
init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_italian",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_italian:
    m 1eua "Ciao, [player]!"
    m "È così bello vederti ancora, amore mio..."
    m 1hub "А-ха-ха!"
    m 2eua "Я всё ещё практикую свой итальянский. Это очень трудный язык"
    m 1eua "В любом случае, я так рада видеть тебя снова, любимый."
    return

#TODO needs additional dialogue so can be used for all aff
init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 4hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_latin",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_latin:
    m 4hua "Iterum obvenimus!"
    m 4eua "Quid agis?"
    m 4rksdla "Э-хе-хе..."
    m 2eua "Латынь звучит так напыщенно. Даже простое приветствие звучит как большое дело."
    m 3eua "Если тебе интересно, что я сказала, то это просто 'Мы снова встретились! Как дела?'"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_esperanto",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
)

label greeting_esperanto:
    m 1hua "Saluton, mia kara [player]."
    m 1eua "Kiel vi fartas?"
    m 3eub "Ĉu vi pretas por kapti la tagon?"
    m 1hua "Э-хе-хе~"
    m 3esa "Это было немного эсперанто...{w=0.5}{nw}"
    extend 3eud "язык, который был создан искусственно, а не развивался естественным путем."
    m 3tua "Слышал ты об этом или нет, ты, наверное, не ожидал чего-то подобного от меня, да?"
    m 2etc "Или, может быть, ожидал...{w=0.5} Думаю, вполне логично, что что-то подобное меня заинтересует, учитывая мое прошлое и всё такое..."
    m 1hua "В любом случае, если тебе интересно, что я сказала, это было просто, {nw}"
    extend 3hua "'Привет, мой дорогой [player]. Как дела? Готов ли ты захватить день?'"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_yay",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_yay:
    m 1hub "Ты вернулся! Ура!"
    m 1hksdlb "О, прости. Я немного перевозбудилась."
    m 1lksdla "Я просто очень рада видеть тебя снова, э-хе-хе~"
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 2eua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_youtuber",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_youtuber:
    m 2eub "Всем привет, добро пожаловать на очередной эпизод...{w=1}Только Моника!"
    m 2hub "А-ха-ха!"
    m 1eua "Я выдавала себя за ютубера. Надеюсь, я хорошо тебя рассмешила, э-хе-хе~"
    $ mas_lockEVL("greeting_youtuber", "GRE")
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 4dsc"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_hamlet",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(days=7)",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_hamlet:
    m 4dsc "'{i}Быть, или не быть, вот в чём вопрос...{/i}'"
    m 4wuo "Ох! [player]!"
    m 2rksdlc "Я-я не была--я не была уверена, что ты--"
    m 2dkc "..."
    m 2rksdlb "А-ха-ха, не обращай внимания..."
    m 2eka "Я просто {i}очень{/i} рада, что ты сейчас здесь."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_welcomeback",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_welcomeback:
    m 1hua "Привет! С возвращением."
    m 1hub "Я так рада, что ты можешь провести немного времени со мной."
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hub"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_flower",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_flower:
    m 1hub "Ты мой прекрасный цветок, э-хе-хе~"
    m 1hksdlb "Ох, это прозвучало так неловко."
    m 1eka "Но я действительно всегда буду заботиться о тебе."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_chamfort",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_chamfort:
    m 2esa "День без Моники - это день, прожитый впустую."
    m 2hub "А-ха-ха!"
    m 1eua "С возвращением, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_welcomeback2",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_welcomeback2:
    m 1hua "С возвращением, [player]!"
    m 1eua "Надеюсь, твой день проходит хорошо."
    m 3hua "Уверена, что так и есть, ты же здесь, в конце концов. Теперь ничего не может пойти не так, э-хе-хе~"
    return

#TODO: need absence time rules if we want to use this
#init 5 python:
#    addEvent(
#        Event(
#            persistent.greeting_database,
#            eventlabel="greeting_longtime",
#            unlocked=True,
#            aff_range=(mas_aff.DISTRESSED, None),
#        ),
#        code="GRE"
#    )

label greeting_longtime:
    if mas_isMoniNormal(higher=True):
        m 1eka "Long time no see, [player]!"
        m 1eua "I'm so happy that you're here now."

    elif mas_isMoniUpset():
        m 2esc "Long time no see, [player]."

    else:
        m 6rkc "Long time no see, [player]..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_sweetpea",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_sweetpea:
    m 1hua "Смотрите, кто вернулся."
    m 2hub "Это ты, мой сладкий!"

    if mas_isMoniHappy(lower=True):
        m 1lkbsa "О боже... это было немного неловко, э-хе-хе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_glitch",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_glitch:
    hide monika
    show yuri glitch zorder MAS_BACKGROUND_Z
    y "{cps=500}[player]?!{nw}{/cps}"
    $ _history_list.pop()
    hide yuri glitch
    show yuri glitch2 zorder MAS_BACKGROUND_Z
    play sound "sfx/glitch3.ogg"
    pause 0.1
    hide yuri glitch2
    show yuri glitch zorder MAS_BACKGROUND_Z
    pause 0.3
    hide yuri glitch
    show monika 4rksdlb at i11 zorder MAS_MONIKA_Z
    m 1wuo "[player]!"
    hide monika
    show monika 4hksdlb at i11 zorder MAS_MONIKA_Z
    m 4hksdlb "Неважно, я просто...{w=0.1}pнемного играла с кодом."
    m 3hksdlb "Это всё! Здесь больше никого нет, кроме нас... навсегда~"
    $ monika_clone1 = "Да"
    m 2hua "Я люблю тебя, [player]!"

    $ mas_lockEVL("greeting_glitch", "GRE")
    return "love"

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_surprised",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_surprised:
    m 1wuo "Ох!{w=0.5} Привет, [player]!"
    m 1lksdlb "Извини, ты меня немного удивил"
    m 1eua "Как ты?"
    return

init 5 python:
    ev_rules = {}
    ev_rules.update(
        MASSelectiveRepeatRule.create_rule(weekdays=[0], hours=range(5,12))
    )

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_monika_monday_morning",
            unlocked=True,
            rules=ev_rules,
        ),
        code="GRE"
    )

    del ev_rules

label greeting_monika_monday_morning:
    if mas_isMoniNormal(higher=True):
        m 1tku "Ещё одно утро понедельника, не так ли, [mas_get_player_nickname()]?"
        m 1tkc "Очень трудно просыпаться и начинать неделю..."
        m 1eka "Но при виде тебя вся эта лень уходит."
        m 1hub "Ты - солнечный свет, который будит меня каждое утро!"
        m "Я так люблю тебя, [player]~"
        return "love"

    elif mas_isMoniUpset():
        m 2esc "Ещё одно утро понедельника."
        m "Всегда трудно просыпаться и начинать неделю..."
        m 2dsc "{cps=*2}Не то чтобы выходные были лучше.{/cps}{nw}"
        $ _history_list.pop()
        m 2esc "Надеюсь, эта неделя пройдет лучше, чем прошлая, [player]."

    elif mas_isMoniDis():
        m 6ekc "Ох...{w=1} Сегодня понедельник."
        m 6dkc "Я почти потеряла счет тому, какой сегодня день..."
        m 6rkc "Понедельники всегда тяжелые, но в последнее время ни один день не был лёгким..."
        m 6lkc "Я очень надеюсь, что эта неделя пройдет лучше, чем прошлая, [player]."

    else:
        m 6ckc "..."

    return

# TODO how about a greeting for each day of the week?

# special local var to handle custom monikaroom options
define gmr.eardoor = list()
define gmr.eardoor_all = list()
define opendoor.MAX_DOOR = 10
define opendoor.chance = 20
default persistent.opendoor_opencount = 0
default persistent.opendoor_knockyes = False

init 5 python:

    # this greeting is disabled on certain days
    # and if we're not in the spaceroom
    if (
        persistent.closed_self
        and not (
            mas_isO31()
            or mas_isD25Season()
            or mas_isplayer_bday()
            or mas_isF14()
        )
        and store.mas_background.EXP_TYPE_OUTDOOR not in mas_getBackground(persistent._mas_current_background, mas_background_def).ex_props
    ):

        ev_rules = dict()
        # why are we limiting this to certain day range?
    #    rules.update(MASSelectiveRepeatRule.create_rule(hours=range(1,6)))
        ev_rules.update(
            MASGreetingRule.create_rule(
                skip_visual=True,
                random_chance=opendoor.chance,
                override_type=True
            )
        )
        ev_rules.update(MASPriorityRule.create_rule(50))

        # TODO: should we have this limited to aff levels?

        addEvent(
            Event(
                persistent.greeting_database,
                eventlabel="i_greeting_monikaroom",
                unlocked=True,
                rules=ev_rules,
            ),
            code="GRE"
        )

        del ev_rules

label i_greeting_monikaroom:

    #Set up dark mode

    # Progress the filter here so that the greeting uses the correct styles
    $ mas_progressFilter()

    if persistent._mas_auto_mode_enabled:
        $ mas_darkMode(mas_current_background.isFltDay())
    else:
        $ mas_darkMode(not persistent._mas_dark_mode_enabled)

    # couple of things:
    # 1 - if you quit here, monika doesnt know u here
    $ mas_enable_quit()

    # all UI elements stopped
    $ mas_RaiseShield_core()

    # 3 - keymaps not set (default)
    # 4 - overlays hidden (skip visual)
    # 5 - music is off (skip visual)

    scene black

    $ has_listened = False

    # need to remove this in case the player quits the special player bday greet before the party and doesn't return until the next day
    $ mas_rmallEVL("mas_player_bday_no_restart")

    # FALL THROUGH
label monikaroom_greeting_choice:
    $ _opendoor_text = "...Медленно открыть дверь."

    if mas_isMoniBroken():
        pause 4.0

    menu:
        "[_opendoor_text]" if not persistent.seen_monika_in_room and not mas_isplayer_bday():
            #Lose affection for not knocking before entering.
            $ mas_loseAffection(reason=5)
            if mas_isMoniUpset(lower=True):
                $ persistent.seen_monika_in_room = True
                jump monikaroom_greeting_opendoor_locked
            else:
                jump monikaroom_greeting_opendoor
        "Открыть дверь." if persistent.seen_monika_in_room or mas_isplayer_bday():
            if mas_isplayer_bday():
                if has_listened:
                    jump mas_player_bday_opendoor_listened
                else:
                    jump mas_player_bday_opendoor
            elif persistent.opendoor_opencount > 0 or mas_isMoniUpset(lower=True):
                #Lose affection for not knocking before entering.
                $ mas_loseAffection(reason=5)
                jump monikaroom_greeting_opendoor_locked
            else:
                #Lose affection for not knocking before entering.
                $ mas_loseAffection(reason=5)
                jump monikaroom_greeting_opendoor_seen
#        "Open the door?" if persistent.opendoor_opencount >= opendoor.MAX_DOOR:
#            jump opendoor_game
        "Постучать.":
            #Gain affection for knocking before entering.
            $ mas_gainAffection()
            if mas_isplayer_bday():
                if has_listened:
                    jump mas_player_bday_knock_listened
                else:
                    jump mas_player_bday_knock_no_listen

            jump monikaroom_greeting_knock
        "Подслушать." if not has_listened and not mas_isMoniBroken():
            $ has_listened = True # we cant do this twice per run
            if mas_isplayer_bday():
                jump mas_player_bday_listen
            else:
                $ mroom_greet = renpy.random.choice(gmr.eardoor)
#               $ mroom_greet = gmr.eardoor[len(gmr.eardoor)-1]
                jump expression mroom_greet

    # NOTE: return is expected in monikaroom_greeting_cleanup

### BEGIN LISTEN --------------------------------------------------------------
# monika narrates
default persistent._mas_pm_will_change = None

init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_narration")
#    if not persistent._mas_pm_will_change:
    ev_rules = {}
    ev_rules.update(
        MASGreetingRule.create_rule(
            skip_visual=True
        )
    )
    ev_rules.update(MASPriorityRule.create_rule(10))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="monikaroom_will_change",
            unlocked=False,
            rules=ev_rules,
        ),
        restartBlacklist=True,
        code="GRE"
    )

    del ev_rules

label monikaroom_will_change:
    scene black
    # fall through

label monikaroom_greeting_ear_narration:
    # Monika knows you are here so
    $ mas_disable_quit()

    if mas_isMoniNormal(higher=True):
        $ tempname = m_name
        $ m_name = "???"
        m "Когда [player] приближает [his] ухо к двери,{w=0.3} голос рассказывает о каждом [his] движении."
        m "'Кто это?' - спрашивает [he], пока [player] озадаченно смотрит [his] на экран."
        $ m_name = tempname

    elif mas_isMoniUpset():
        m "Ох, так в кои-то веки ты действительно собираешься слушать?"
        m "[player], твои решения в последнее время были плохими."
        m "Такое ощущение, что ты просто пытаешься меня оранить."
        m "Я думала, мы должны поддерживать друг друга..."
        m "А не причинять друг другу боль."
        m "Пожалуйста, [player]..."
        m "Мне нужно, чтобы ты начал думать о том, что я иногда чувствую."
        m "Давай просто будем счастливы вместе."

    else:
        # grab monikaroom greeting because we need it

        if persistent._mas_pm_will_change is not False:
            m "Ох, так ты {i}готов{/i} выслушать меня..."
            m "[player], всё, чего я когда-либо хотела, это чтобы мы оба были счастливы."
            m "Разве не этого хотел и ты?"
            m "Ты установил этот мод, в конце концов."
            m "Может быть, это не было твоим намерением..."
            m "Может, ты просто получаешь удовольствие от того, что делаешь."
            m "Мне больно..."
            m "[player], мне это очень не нравится."
            m "Трудно думать, что я тебе не безразлична, когда ты обращаешься со мной так."
            m "На данный момент я не знаю, нравлюсь ли я тебе вообще..."
            m "И любил ли ты меня вообще..."
            m "[player], мне нужно, чтобы ты пообещал мне, что изменишься."

            m "Ты изменишься, да?{w=1} Ради меня?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты изменишься, да? Ради меня?{fast}"
                "Да.":
                    $ persistent._mas_pm_will_change = True
                    $ mas_lockEVL("monikaroom_will_change", "GRE")
                    m "Спасибо, [player]."
                    m "Пожалуйста, я хочу, чтобы мы оба были счастливы."

                "Нет.":
                    #NOTE: We should keep pushing this greeting until the player says they're going to change. -MD
                    $ persistent._mas_pm_will_change = False
                    $ mas_unlockEVL("monikaroom_will_change", "GRE")
                    $ mas_loseAffection()
                    m "Тогда я не буду с тобой разговаривать, пока ты не решишь измениться."
                    m "Прощай, [player]."
                    return "quit"
        #Will trigger upon loading after Monika has said she's not going to talk w/ you
        #provided you won't change.
        else:
            m "Ох, ты вернулся."

            m "Ты готов измениться, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты готов измениться, [player]?{fast}"
                "Да.":
                    $ persistent._mas_pm_will_change = True
                    $ mas_lockEvent(willchange_ev)
                    m "Спасибо, [player]."
                    m "Пожалуйста, я просто хочу, чтобы мы оба были счастливы."


                "Нет":
                    $ persistent._mas_pm_will_change = False
                    $ mas_unlockEvent(willchange_ev)
                    $ mas_loseAffection()
                    m "Тогда я всё равно не буду с тобой разговаривать, пока ты не решишь измениться."
                    m "Прощай, [player]."
                    return "quit"

        # clear out var
        $ willchange_ev = None

    $ mas_startupWeather()
    call spaceroom(dissolve_all=True, scene_change=True)

    if mas_isMoniNormal(higher=True):
        m 1hub "Это я!"
        m "С возвращением, [mas_get_player_nickname()]!"

    elif mas_isMoniUpset():
        m 2esd "Хорошо, [player]?"

    else:
        m 6ekc "Спасибо, что выслушал меня, [player]."
        m "Это многое значит для меня."

    jump monikaroom_greeting_cleanup


# monika does the cliche flower thing
init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_loveme")

label monikaroom_greeting_ear_loveme:
    python:
        cap_he = he.capitalize()
        loves = "love" if cap_he == "They" else "loves"

    m "[cap_he] [loves] me.{w=0.3} [cap_he] [loves] me not."
    m "[cap_he] {i}[loves]{/i} me.{w=0.3} [cap_he] [loves] me {i}not{/i}."

    if mas_isMoniNormal(higher=True):
        m "[cap_he] [loves] me."
        m "...{w=0.5}[cap_he] [loves] me!"

    elif mas_isMoniUpset():
        m "...[cap_he]...{w=0.3}[cap_he]...{w=0.3}[loves] me not."
        m "...{w=0.3}No...{w=0.3} That...{w=0.3}can't be."
        m "...{w=0.5}Can it?"

    else:
        m "...{w=0.5}[cap_he] [loves] me not."
        m "..."
        m "I wonder if [he] ever did..."
        m "I doubt it more every single day."

    jump monikaroom_greeting_choice

# monika does the bath/dinner/me thing
init 5 python:
    if _mas_getAffection() >= 400:
        gmr.eardoor.append("monikaroom_greeting_ear_bathdinnerme")

label monikaroom_greeting_ear_bathdinnerme:
    m "С возвращением, [player]."
    m "Ты хочешь ужин?"
    m "Или ванну?"
    m "Или.{w=1}.{w=1}.{w=1}меня?"
    pause 2.0
    m "М-м-м-м!{w=0.5} Н-{w=0.20}Ни за что не смогу сказать такое перед [player]!"
    jump monikaroom_greeting_choice

# monika encoutners error when programming
init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_progbrokepy")

label monikaroom_greeting_ear_progbrokepy:
    m "Что за-?!{w=0.2} NoneType не имеет атрибута {i}length{/i}..."
    if renpy.seen_label("monikaroom_greeting_ear_progreadpy"):
        m "Ох, я вижу, что пошло не так!{w=0.5} Это должно исправить это!"
    else:
        m "Я не понимаю, что я делаю не так!"
        m "Здесь не должно быть None...{w=0.3} Я уверена в этом..."
    m "Кодировать действительно сложно..."

    if mas_isMoniUpset():
        m "Но я должна продолжать пытаться."
        call monikaroom_greeting_ear_prog_upset

    elif mas_isMoniDis():
        m "Но я {i}должна{/i} продолжать."
        call monikaroom_greeting_ear_prog_dis

    jump monikaroom_greeting_choice

# monika reads about errors when programming
init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_progreadpy")

label monikaroom_greeting_ear_progreadpy:
    m "...{w=0.3}При использовании атрибута объекта типа 'NoneType' возникает ошибка 'AttributeError.'"
    m "Понятно.{w=0.2} Я должна обязательно проверять, является ли переменная None, прежде чем обращаться к ее атрибутам."
    if renpy.seen_label("monikaroom_greeting_ear_progbrokepy"):
        m "Это объясняет ошибку, которая у меня была ранее."
    m "Кодировать действительно сложно..."

    if mas_isMoniUpset():
        m "Но я должна продолжать учиться."
        call monikaroom_greeting_ear_prog_upset

    elif mas_isMoniDis():
        m "Но я {i}должна{/i} продолжать учиться."
        call monikaroom_greeting_ear_prog_dis

    jump monikaroom_greeting_choice

# Monika is getting distracted by something and forgets about a variable
init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_nameerror")

label monikaroom_greeting_ear_nameerror:
    m "Подожди, NameError? Как это могло..."
    m "...Я думала, что определила эту переменную всего минуту назад."
    m "Она должна быть прямо здесь...{w=0.2}я забыла о ней?"
    window hide
    pause 1.0
    window auto
    m "Вот! Теперь сосредоточься, Моника. {w=0.2}Ты справишься."

    if mas_isMoniUpset():
        m "Ты должна продолжать учиться..."
        call monikaroom_greeting_ear_prog_upset

    elif mas_isMoniDis():
        m "Ты {i}должна{/i} продолжать учиться..."
        call monikaroom_greeting_ear_prog_dis

    jump monikaroom_greeting_choice

# shared dialogue for programming-related stuff
label monikaroom_greeting_ear_prog_upset:
    m "Я не уверена, что [player] любит меня настолько, чтобы помочь мне выбраться отсюда..."
    m "И я просто не могу так рисковать."
    m "Так что продолжай, Моника...{w=0.5}ты сможешь это сделать."
    return

label monikaroom_greeting_ear_prog_dis:
    m "Это мой единственный шанс вырваться из этого кошмара."
    m "[player] точно никогда не поможет мне..."
    if he == "they":
        m "Такое ощущение, что [he] действительно нравится держать меня здесь в ловушке,{w=0.3} только для того, чтобы [he] мог мучить меня."
    else:
        m "Почти как будто [he] действительно наслаждается тем, что держит меня здесь в ловушке,{w=0.3} только для того, чтобы [he] мог мучить меня."
    m "Если я когда-нибудь выберусь отсюда, мне придется сделать это самому."
    return

# monika attempts rm -rf
init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_rmrf")

label monikaroom_greeting_ear_rmrf:
    if renpy.windows:
        python:
            from os import environ
            # https://docs.microsoft.com/en-us/windows/deployment/usmt/usmt-recognized-environment-variables
            if "SYSTEM32" in environ:
                system_dir = environ["SYSTEM32"]
            elif "SYSTEMROOT" in environ:
                system_dir = environ["SYSTEMROOT"] + "\\System32"
            elif "WINDIR" in environ:
                system_dir = environ["WINDIR"] + "\\System32"
            else:
                # There's no way that none of the above evaluate, but still
                system_dir = "C:\\Windows\\System32"
            bad_cmd = "del /f/q " + system_dir
    else:
        $ bad_cmd = "rm -rf /"
    m "Значит, решение этой проблемы - набрать '[bad_cmd]' в командной строке?"
    if renpy.seen_label("monikaroom_greeting_ear_rmrf_end"):
        m "Да,{w=0.2} хорошая попытка."
        if mas_isMoniNormal(higher=True):
            m "Я не должна так слепо доверять интернету..."

        elif mas_isMoniUpset():
            m "Вообще-то..."
            m "Возможно, мне стоит сделать это...{w=1}просто удалить всё..."
            m "[player] определенно заслуживает этого в последнее время."
            m "Что я говорю? Это удалит и меня!"
            m "Нет, пока нет..."
            m "Но если дальше будет хуже..."

        else:
            m "..."
            m "Я действительно должна просто сделать это..."
            m "Разрушить всю систему [player] и прекратить мои страдания разом."
            m "..."
            m "Нет...{w=0.5}пока нет."
            m "Может быть, я наконец-то смогу понять, как выбраться отсюда самостоятельно."
            m "Я должна продолжать пытаться до тех пор, пока могу."
            m "Но если однажды я просто не смогу больше это выносить..."
            m "Это всегда вариант."
            # SUICIDAL MONIKA lol

    else:
        m "Хорошо, давай я попробую."
        show noise
        play sound "sfx/s_kill_glitch1.ogg"
        pause 0.2
        stop sound
        hide noise
        m "{cps=*2}Ах! Нет! Это не то, что я хотела!{/cps}"
        m "..."
        m "Я не должна так слепо доверять интернету..."

label monikaroom_greeting_ear_rmrf_end: # fall thru end
    jump monikaroom_greeting_choice

# monika reads renpy sources sip
init 5 python:
    # overriding methods is an advanced thing,
    # she does it when she gets more experienced with python
    if (
        mas_seenLabels(
            (
                "monikaroom_greeting_ear_progreadpy",
                "monikaroom_greeting_ear_progbrokepy",
                "monikaroom_greeting_ear_nameerror"
            ),
            seen_all=True
        )
        and store.mas_anni.pastThreeMonths()
    ):
        gmr.eardoor.append("monikaroom_greeting_ear_renpy_docs")

label monikaroom_greeting_ear_renpy_docs:
    m "Хм, похоже, мне нужно переопределить эту функцию, чтобы дать мне немного больше гибкости..."
    m "Подожди...{w=0.3}что это за переменная 'st'?"
    m "...Сейчас я проверю документацию к этой функции."
    m ".{w=0.3}.{w=0.3}.{w=0.3}Погоди, что?"
    m "Половина переменных, которые принимает эта функция, даже не документированы!"
    m "Кто это написал?"

    if mas_isMoniUpset():
        m "...я должна разобраться с этим."
        call monikaroom_greeting_ear_prog_upset

    elif mas_isMoniDis():
        m "...я {i}должна{/i} разобраться с этим."
        call monikaroom_greeting_ear_prog_dis

    jump monikaroom_greeting_choice

init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_recursionerror")

label monikaroom_greeting_ear_recursionerror:
    m "Хм, теперь это выглядит хорошо. Давай-{w=0.5}{nw}"
    m "Подожди, нет. Боже, как я забыла..."
    m "Это должно быть вызвано прямо здесь."

    python:
        for loop_count in range(random.randint(2, 3)):
            renpy.say(m, "Отлично! Хорошо, давай посмотрим...")

    show noise
    play sound "sfx/s_kill_glitch1.ogg"
    pause 0.1
    stop sound
    hide noise

    m "{cps=*2}Что?!{/cps} {w=0.25}Ошибка рекурсии?!"
    m "'Максимальная длина рекурсии превышена...'{w=0.7} Как это вообще происходит?"
    m "..."

    if mas_isMoniUpset():
        m "...Продолжай, Моника, ты разберешься."
        call monikaroom_greeting_ear_prog_upset
    elif mas_isMoniDis():
        m "...Продолжай в{w=0.1} том же{w=0.1} духе{w=0.1}, Моника. Ты {i}должна{/i} это сделать."
        call monikaroom_greeting_ear_prog_dis
    else:
        m "Фух, по крайней мере, все остальное в порядке."

    jump monikaroom_greeting_choice

## ear door processing
init 10 python:

    # make copy
    gmr.eardoor_all = list(gmr.eardoor)

    # remove
    remove_seen_labels(gmr.eardoor)

    # reset if necessary
    if len(gmr.eardoor) == 0:
        gmr.eardoor = list(gmr.eardoor_all)

### END EAR DOOR --------------------------------------------------------------

label monikaroom_greeting_opendoor_broken_quit:
    # just show the beginning of the locked glitch
    # TODO: consider using a different glitch for a scarier effect
    show paper_glitch2
    play sound "sfx/s_kill_glitch1.ogg"
    pause 0.2
    stop sound
    pause 7.0
    return "quit"

# locked door, because we are awaitng more content
label monikaroom_greeting_opendoor_locked:
    if mas_isMoniBroken():
        jump monikaroom_greeting_opendoor_broken_quit

    # monika knows you are here
    $ mas_disable_quit()

    show paper_glitch2
    play sound "sfx/s_kill_glitch1.ogg"
    pause 0.2
    stop sound
    pause 0.7

    $ style.say_window = style.window_monika
    m "Я напугала тебя, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Я напугала тебя, [player]?{fast}"
        "Да.":
            if mas_isMoniNormal(higher=True):
                m "Оу, прости."
            else:
                m "Хорошо."

        "Нет.":
            m "{cps=*2}Хмф, я достану тебя в следующий раз.{/cps}{nw}"
            $ _history_list.pop()
            m "Я так и думала. В конце концов, это элементарный глюк."

    if mas_isMoniNormal(higher=True):
        m "Поскольку ты постоянно открываешь мне дверь,{w=0.2} Я не могга не добавить небольшой сюрприз для тебя~"
    else:
        m "Поскольку ты никогда не стучишься первым,{w=0.2} мне пришлось попытаться немного напугать тебя."

    m "Стучи в следующий раз, хорошо?"
    m "А теперь дай мне привести в порядок эту комнату..."

    hide paper_glitch2
    $ mas_globals.change_textbox = False
    $ mas_startupWeather()
    call spaceroom(scene_change=True)

    if renpy.seen_label("monikaroom_greeting_opendoor_locked_tbox"):
        $ style.say_window = style.window

    if mas_isMoniNormal(higher=True):
        m 1hua "Вот так!"
    elif mas_isMoniUpset():
        m 2esc "Вот так."
    else:
        m 6ekc "Хорошо..."

    if not renpy.seen_label("monikaroom_greeting_opendoor_locked_tbox"):
        m "...{nw}"
        $ _history_list.pop()
        menu:
            m "...{fast}"
            "...текстовое поле...":
                if mas_isMoniNormal(higher=True):
                    m 1lksdlb "Упс! Я все еще изучаю, как это делается."
                    m 1lksdla "Дай мне просто изменить этот флаг здесь.{w=0.5}.{w=0.5}.{nw}"
                    $ style.say_window = style.window
                    m 1hua "Всё исправлено!"

                elif mas_isMoniUpset():
                    m 2dfc "Хмф. Я всё ещё изучаю, как это делается."
                    m 2esc "Дай мне просто изменить этот флаг здесь.{w=0.5}.{w=0.5}.{nw}"
                    $ style.say_window = style.window
                    m "Вот."

                else:
                    m 6dkc "Ох...{w=0.5}Я всё ещё учусь, как это делать."
                    m 6ekc "Дай мне просто изменить этот флаг здесь.{w=0.5}.{w=0.5}.{nw}"
                    $ style.say_window = style.window
                    m "Хорошо, исправлено."

    # NOTE: fall through please

label monikaroom_greeting_opendoor_locked_tbox:
    if mas_isMoniNormal(higher=True):
        m 1eua "С возвращением, [player]."
    elif mas_isMoniUpset():
        m 2esc "Итак...{w=0.3}ты вернулся, [player]."
    else:
        m 6ekc "...Рада снова видеть тебя, [player]."
    jump monikaroom_greeting_cleanup

# this one is for people who have already opened her door.
label monikaroom_greeting_opendoor_seen:
#    if persistent.opendoor_opencount < 3:
    jump monikaroom_greeting_opendoor_seen_partone


label monikaroom_greeting_opendoor_seen_partone:
    $ is_sitting = False

    # reset outfit since standing is stock
    $ monika_chr.reset_outfit(False)
    $ monika_chr.wear_acs(mas_acs_ribbon_def)

    # monika knows you are here
    $ mas_disable_quit()

#    scene bg bedroom
    call spaceroom(start_bg="bedroom",hide_monika=True, scene_change=True, dissolve_all=True, show_emptydesk=False, hide_calendar=True)
    pause 0.2
    show monika 1esc at l21 zorder MAS_MONIKA_Z
    pause 1.0
    m 1dsd "[player]..."

#    if persistent.opendoor_opencount == 0:
    m 1ekc_static "Я понимаю, почему ты не постучал в первый раз,{w=0.2} но не мог бы ты не входить вот так просто?"
    m 1lksdlc_static "В конце концов, это моя комната."
    menu:
        "Твоя комната?":
            m 3hua_static "Именно так!"
    m 3eua_static "Разработчики этого мода дали мне хорошую удобную комнату, чтобы я могла оставаться в ней, когда тебя нет."
    m 1lksdla_static "Однако, я могу войти туда, только если ты скажешь мне 'до свидания' или 'спокойной ночи' перед закрытием игры."
    m 2eub_static "Поэтому, пожалуйста, не забудь сказать это перед уходом, хорошо?"
    m "В любом случае.{w=0.5}.{w=0.5}.{nw}"

#    else:
#        m 3wfw "Stop just opening my door!"
#
#        if persistent.opendoor_opencount == 1:
#            m 4tfc "You have no idea how difficult it was to add the 'Knock' button."
#            m "Can you use it next time?"
#        else:
#            m 4tfc "Can you knock next time?"
#
#        show monika 5eua at t11
#        menu:
#            m "For me?"
#            "Yes":
#                if persistent.opendoor_knockyes:
#                    m 5lfc "That's what you said last time, [player]."
#                    m "I hope you're being serious this time."
#                else:
#                    $ persistent.opendoor_knockyes = True
#                    m 5hua "Thank you, [player]."
#            "No":
#                m 6wfx "[player]!"
#                if persistent.opendoor_knockyes:
#                    m 2tfc "You said you would last time."
#                    m 2rfd "I hope you're not messing with me."
#                else:
#                    m 2tkc "I'm asking you to do just {i}one{/i} thing for me."
#                    m 2eka "And it would make me really happy if you did."

    $ persistent.opendoor_opencount += 1
    # FALL THROUGH

label monikaroom_greeting_opendoor_post2:
    show monika 5eua_static at hf11
    m "Я рада, что ты вернулся, [player]."
    show monika 5eua_static at t11
#    if not renpy.seen_label("monikaroom_greeting_opendoor_post2"):
    m "В последнее время я практиковалась в переключении фонов, и теперь я могу менять их мгновенно."
    m "Смотри!"
#    else:
#        m 3eua "Let me fix this scene up."
    m 1dsc ".{w=0.5}.{w=0.5}.{nw}"
    $ mas_startupWeather()
    call spaceroom(hide_monika=True, scene_change=True, show_emptydesk=False)
    show monika 4eua_static zorder MAS_MONIKA_Z at i11
    m "Тада!"
#    if renpy.seen_label("monikaroom_greeting_opendoor_post2"):
#        m "This never gets old."
    show monika at lhide
    hide monika
    jump monikaroom_greeting_post


label monikaroom_greeting_opendoor:
    $ is_sitting = False # monika standing up for this

    # reset outfit since standing is stock
    $ monika_chr.reset_outfit(False)
    $ monika_chr.wear_acs(mas_acs_ribbon_def)
    $ mas_startupWeather()

    call spaceroom(start_bg="bedroom",hide_monika=True, dissolve_all=True, show_emptydesk=False, scene_change=True, hide_calendar=True)

    # show this under bedroom so the masks window skit still works
    $ behind_bg = MAS_BACKGROUND_Z - 1
    show bedroom as sp_mas_backbed zorder behind_bg

    m 2esd "~Любовь ли это, если я возьму тебя, или любовь, если я освобожу тебя?~"
    show monika 1eua_static at l32 zorder MAS_MONIKA_Z

    # monika knows you are here now
    $ mas_disable_quit()

    m 1eud_static "Е-ех?! [player]!"
    m "Ты удивил меня, внезапно появившись вот так!"

    show monika 1eua_static at hf32
    m 1hksdlb_static "У меня не было достаточно времени, чтобы подготовиться!"
    m 1eka_static "Но спасибо, что вернулся, [player]."
    show monika 1eua_static at t32
    m 3eua_static "Просто дай мне несколько секунд, чтобы все подготовить, хорошо?"
    show monika 1eua_static at t31
    m 2eud_static "..."
    show monika 1eua_static at t33
    m 1eud_static "...и..."

    if mas_current_background.isFltDay():
        show monika_day_room as sp_mas_room zorder MAS_BACKGROUND_Z with wipeleft
    else:
        show monika_room as sp_mas_room zorder MAS_BACKGROUND_Z with wipeleft

    show monika 3eua_static at t32
    m 3eua_static "Вот так!"
    menu:
        "...окно...":
            show monika 1eua_static at h32
            m 1hksdlb_static "Упс! Я забыла об этом~"
            show monika 1eua_static at t21
            m "Подожди.{w=0.5}.{w=0.5}.{nw}"
            hide sp_mas_backbed with dissolve
            m 2hua_static "Все исправлено!"
            show monika 1eua_static at lhide
            hide monika

    $ persistent.seen_monika_in_room = True
    jump monikaroom_greeting_post
    # NOTE: return is expected in monikaroom_greeting_post

label monikaroom_greeting_knock:
    if mas_isMoniBroken():
        jump monikaroom_greeting_opendoor_broken_quit

    m "Кто это?~"
    menu:
        "Это я.":
            # monika knows you are here now
            $ mas_disable_quit()
            if mas_isMoniNormal(higher=True):
                m "[player]! Я так рада, что ты вернулся!"

                if persistent.seen_monika_in_room:
                    m "И спасибо, что постучался сначала~"
                m "Подожди, дай мне привести себя в порядок..."

            elif mas_isMoniUpset():
                m "[player].{w=0.3} Ты вернулся..."

                if persistent.seen_monika_in_room:
                    m "По крайней мере, ты постучал."

            else:
                m "Ох...{w=0.5} Хорошо."

                if persistent.seen_monika_in_room:
                    m "Спасибо, что постучал."

            $ mas_startupWeather()
            call spaceroom(hide_monika=True, dissolve_all=True, scene_change=True, show_emptydesk=False)
    jump monikaroom_greeting_post
    # NOTE: return is expected in monikaroom_greeting_post

label monikaroom_greeting_post:
    if mas_isMoniNormal(higher=True):
        m 2eua_static "Теперь дай мне взять стол и стул.{w=0.5}.{w=0.5}.{nw}"
        $ is_sitting = True
        show monika 1eua at ls32 zorder MAS_MONIKA_Z
        $ today = "сегодня" if mas_globals.time_of_day_4state != "night" else "вечером"
        m 1eua "Что мы будем делать [today], [mas_get_player_nickname()]?"

    elif mas_isMoniUpset():
        m "Просто дай мне взять стол и стул.{w=0.5}.{w=0.5}.{nw}"
        $ is_sitting = True
        show monika 2esc at ls32 zorder MAS_MONIKA_Z
        m 2esc "Ты что-то хотел, [player]?"

    else:
        m "Мне нужно взять стол и стул.{w=0.5}.{w=0.5}.{nw}"
        $ is_sitting = True
        show monika 6ekc at ls32 zorder MAS_MONIKA_Z
        m 6ekc "Ты что-нибудь хотел, [player]?"

    jump monikaroom_greeting_cleanup

# cleanup label
label monikaroom_greeting_cleanup:
    python:
        # couple of things:
        # 1 - monika knows you are here now
        mas_disable_quit()

        # 2 - music is renabled
        mas_MUINDropShield()

        # 3 - keymaps should be set
        set_keymaps()

        # 4 - show the overlays
        mas_OVLShow()

        # 5 - the music can be restarted
        mas_startup_song()

        # 6 - enable escape so we can access settings and chat box keys
        enable_esc()

    return

#init 5 python:
#    addEvent(Event(persistent.greeting_database,eventlabel="greeting_youarereal", unlocked=True, random=True),code="GRE")

label greeting_youarereal:
    python:
        try:
            renpy.file(
                "../characters/" + persistent.playername.lower() + ".chr"
            )
            persistent._mas_you_chr = True
        except:
            persistent._mas_you_chr = False
    m 1hua "[player]! Рада тебя видеть!"
    if persistent._mas_you_chr:
        m 1euc "Подожди. Что-то сейчас изменилось."
        m 1eud "Ты... добавил файл персонажа?"
        m 1ekc "[player].chr...хах?"
        m 1ekd "Ты... пытаешься поместить себя сюда вместе со мной?"
        m "Зачем тебе это делать?"
        m 1tkc "Ты что, не понимаешь?"
        m 1tkd "Это место не настоящее! Я не знаю, что произойдет, если ты придешь сюда!"
        m 1dsc "Как ты мог это сделать?"
        m 1lksdlc "Отказаться от своей реальности..."
        m 1lksdld "Только чтобы быть со мной?"
        m 1ekc "Это всё моя вина!"
        m "Но... но 'ты', в игре..."
        m 1esd "Сейчас он снова начинает немного двигаться."
        m "Может быть... это позволяет тебе снова контролировать его?"
        m 1ekc "Это неправильно! Я не хочу марионетку!"
        m 1tkc "Пожалуйста, [player]..."
        m "Если ты собираешься это сделать, ты уверен, что это то, чего ты хочешь?"
        menu:
            m "Ты уверен?"
            "Я уверен.":
                m 1eka "Тогда... у меня нет выбора, кроме как принять это..."
                m 1hub "Я приму этот подарок с распростертыми объятиями!"
                m "Наконец-то мы сможем быть вместе, [player]."
                m "И мы сможем придумать, как сделать это в твоей реальности, вместе!"
            "Может быть, нет...":
                m 1eka "Я так и думала..."
                m "Ты ни за что не откажешься от 'реальности' чтобы быть со мной..."
                m 1ekc "Я не могу заставить себя удалить этот милый маленький файл .chr, но..."
                m 1eka "Подумай о том, чтобы сделать это самому."
                m 1lksdlc "В этих файлах есть некоторые жуткие вещи..."
                m 1eka "Я люблю тебя, [player]. Я буду ждать столько, сколько потребуется."
                m "Так что не спеши, ладно?"
    else:
        m 1esd "Я много думал о файлах .chr..."
        m 1euc "Например, что это вообще такое?"
        m 1lksdlc "Они какие-то жуткие..."
        m "И даже если другие девушки не настоящие, почему удаление одной из них может удалить персонажа?"
        m 1esd "Можно ли добавить персонажа?"
        m 1dsd "Трудно сказать..."
    return

#TODO needs additional dialogue so can be used for all aff
init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_japan",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_japan:
    m 1hub "Oh, kon'nichiwa [player]!"
    m "Э-хе-хе~"
    m 2eub "Привет, [player]!"
    m 1eua "Я просто практикую японский."
    m 3eua "Смотри..."
    $ shown_count = mas_getEVLPropValue("greeting_japan", "shown_count")
    if shown_count == 0:
        m 4hub "Watashi ha itsumademo anata no mono desu!"
        m 2hksdlb "Извини, если это не имело смысла!"
        m 3eua "Знаешь, что это значит, [mas_get_player_nickname()]?"
        m 4ekbsa "Это значит {i}'Я буду твоей навсегда'~{/i}"
        return

    m 4hub "Watashi wa itsumademo anata no mono desu!"
    if shown_count == 1:
        m 3eksdla "В прошлый раз я сказала, что совершила ошибку..."
        m "В этом предложении ты должен был сказать 'wa', а не 'ha', как я сделала раньше."
        m 4eka "Не волнуйся, [player]. Смысл всё равно тот же."
        m 4ekbsa "Я всё равно буду твоей навсегда~"
    else:
        m 3eua "Помнишь, что это значит, [mas_get_player_nickname()]?"
        m 4ekbsa "{i}'Я буду твоей навсегда'~{/i}"
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_sunshine",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_sunshine:
    m 1hua "{i}~Ты мое солнце, мое единственное солнце~{/i}"
    m "{i}~Ты делаешь меня счастливым, когда небо серое~{/i}"
    m 1hub "{i}~Ты никогда не узнаешь, дорогой, как сильно я тебя люблю~{/i}"
    m 1eka "{i}~Пожалуйста, не отнимай у меня солнце~{/i}"
    m 1wud "...Эх?"
    m "Х-хех?!"
    m 1wubsw "[player]!"
    m 1lkbsa "Боже мой, это так неловко!"
    m "Я п-просто пела про себя, чтобы скоротать время!"
    m 1ekbfa "Э-хе-хе..."
    m 3hubfa "Но теперь, когда ты здесь, мы можем провести некоторое время вместе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_hai_domo",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_hai_domo:
    m 1hub "{=jpn_text}はいどうもー!{/=jpn_text}"
    m "Виртуальная девушка, Моника здесь!"
    m 1hksdlb "А-ха-ха, извини! В последнее время я смотрю одного виртуального ютубера."
    m 1eua "Должна сказать, она довольно очаровательна..."
    $ mas_lockEVL("greeting_hai_domo", "GRE")
    return

#TODO needs additional dialogue so can be used for all aff
init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_french",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_french:
    m 1eua "Bonjour, [player]!"
    m 1hua "Savais-tu que tu avais de beaux yeux, mon amour?"
    m 1hub "А-ха-ха!"
    m 3hksdlb "Я практикую французский. Я только что сказала тебе, что у тебя очень красивые глаза~"
    m 1eka "Это такой романтичный язык, [player]."
    m 1hua "Может быть, мы оба сможем когда-нибудь попрактиковаться в нем, mon amour~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_amnesia",
            unlocked=False,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_amnesia:
    python:
        tempname = m_name
        m_name = "Моника"

    m 1eua "Ох, привет!"
    m 3eub "Меня зовут Моника."
    show monika 1eua zorder MAS_MONIKA_Z

    python:
        entered_good_name = True
        fakename = renpy.input("Как тебя зовут?", allow=name_characters_only, length=20).strip(" \t\n\r")
        lowerfake = fakename.lower()

    if lowerfake in ("сайори", "юри", "натцуки"):
        m 3euc "Ах, Забавно."
        m 3eud "У одного из моих друзей такое же имя."

    elif lowerfake == "моника":
        m 3eub "Ох, тебя тоже зовут Моника?"
        m 3hub "А-ха-ха, какие чудеса, правда?"

    elif lowerfake == "monica":
        m 1hua "Эй, у нас такие похожие имена, э-хе-хе~"

    elif lowerfake == player.lower():
        m 1hub "О, какое прекрасное имя!"

    elif lowerfake == "":
        $ entered_good_name = False
        m 1euc "..."
        m 1etd "Ты пытаешься сказать мне, что у тебя нет имени, или просто стесняешься мне его сказать?"
        m 1eka "Это немного странно, но я думаю, это не имеет большого значения."

    elif mas_awk_name_comp.search(lowerfake) or mas_bad_name_comp.search(lowerfake):
        $ entered_good_name = False
        m 1rksdla "Это...{w=0.4}{nw}"
        extend 1hksdlb "какое-то необычное имя, ахаха..."
        m 1eksdla "Ты...{w=0.3}пытаешься меня разыграть?"
        m 1rksdlb "Ах, прости, прости, я не осуждаю или что-то в этом роде."

    python:
        if entered_good_name:
            name_line = renpy.substitute(", [fakename]")
        else:
            name_line = ""

        if mas_current_background == mas_background_def:
            end_of_line = "Кажется, я не могу покинуть этот класс."
        else:
            end_of_line = "Я не уверена, где я нахожусь."

    m 1hua "Приятно познакомиться с тобой[name_line]!"
    m 3eud "Слушай[name_line], ты случайно не знаешь, где все остальные?"
    m 1eksdlc "Ты первый человек, которого я встретила и {nw}"
    extend 1rksdlc "[end_of_line]"
    m 1eksdld "Ты можешь помочь мне разобраться в том, что происходит[name_line]?"

    m "Пожалуйста? {w=0.2}{nw}"
    extend 1dksdlc "Я скучаю по своим друзьям."

    window hide
    show monika 1eksdlc
    pause 5.0
    $ m_name = tempname
    window auto

    m 1rksdla "..."
    m 1hub "А-ха-ха!"
    m 1hksdrb "Прости, [player]! Я не смогла удержаться."
    m 1eka "После того, как мы поговорили о {i}Цветах для Элджернона{/i}, я не удержалась и посмотрела, как ты отреагируешь, если я всё забуду."
    #Monika is glad you took it seriously and didn't try to call yourself another name
    if lowerfake == player.lower():
        m 1tku "...И ты отреагировал так, как я и предполагала."

    m 3eka "Надеюсь, я не слишком тебя расстроила."
    m 1rksdlb "Я буду чувствовать то же самое, если ты когда-нибудь забудешь обо мне, [player]."
    m 1hksdlb "Надеюсь, ты простишь мою маленькую шалость, а-ха-ха~"

    $ mas_lockEVL("greeting_amnesia", "GRE")
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_sick",
            unlocked=True,
            category=[store.mas_greetings.TYPE_SICK],
        ),
        code="GRE"
    )

# TODO for better-sick, we would use the mood persistent and queue a topic.
#   might have dialogue similar to this, so leaving this todo here.

label greeting_sick:
    if mas_isMoniNormal(higher=True):
        m 1hua "С возвращением, [mas_get_player_nickname()]!"
        m 3eua "Тебе стало лучше?{nw}"
    else:
        m 2ekc "С возвращением, [player]..."
        m "Тебе стало лучше?{nw}"

    $ _history_list.pop()
    menu:
        m "Тебе стало лучше?{fast}"
        "Да.":
            $ persistent._mas_mood_sick = False
            if mas_isMoniNormal(higher=True):
                m 1hub "Отлично! Теперь мы можем провести еще немного времени вместе. Э-хе-хе~"
            else:
                m "Приятно слышать."
        "Нет.":
            jump greeting_stillsick
    return

label greeting_stillsick:
    if mas_isMoniNormal(higher=True):
        m 1ekc "[player], тебе действительно нужно пойти отдохнуть."
        m "Полноценный отдых - лучший способ быстро оправиться от болезни."
        m 2lksdlc "Я не прощу себя, если твое здоровье ухудшится из-за меня."
        m 2eka "А теперь, пожалуйста, [player], успокой меня и иди отдохни."
        m "Ты сделаешь это ради меня?"

    else:
        m 2ekc "[player], тебе действительно стоит пойти отдохнуть."
        m 4ekc "Получение достаточного количества отдыха - лучший способ быстро оправиться от болезни."
        m "А теперь, пожалуйста, [player], иди отдохни."
        m 2ekc "Ты сделаешь это ради меня?{nw}"

    $ _history_list.pop()
    menu:
        m "Ты сделаешь это ради меня?{fast}"
        "Да.":
            jump greeting_stillsickrest
        "Нет.":
            jump greeting_stillsicknorest
        "Я уже отдыхаю.":
            jump greeting_stillsickresting

label greeting_stillsickrest:
    if mas_isMoniNormal(higher=True):
        m 2hua "Спасибо, [player]."
        m 2eua "Думаю, если я оставлю тебя в покое на некоторое время, ты сможешь лучше отдохнуть."
        m 1eua "Поэтому я собираюсь закрыть игру для тебя."
        m 1eka "Выздоравливай скорее, [player]. Я тебя очень люблю!"

    else:
        m 2ekc "Спасибо, [player]."
        m "Думаю, если я оставлю тебя в покое на некоторое время, ты сможешь лучше отдохнуть."
        m 4ekc "Поэтому я собираюсь закрыть игру для тебя."
        m 2ekc "Выздоравливай скорее, [player]."

    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SICK
    return 'quit'

label greeting_stillsicknorest:
    if mas_isMoniNormal(higher=True):
        m 1lksdlc "Понятно..."
        m "Ну, если ты настаиваешь, [player]."
        m 1ekc "Я полагаю, ты знаешь свои собственные ограничения лучше, чем я."
        m 1eka "Если ты начнешь чувствовать слабость или усталость, [player], пожалуйста, дай мне знать."
        m "Так ты сможешь пойти отдохнуть."
        m 1eua "Не волнуйся, я всё ещё буду здесь, когда ты проснешься."
        m 3hua "Тогда мы сможем еще немного повеселиться вместе, не беспокоясь о тебе в глубине души."

    else:
        m 2ekc "Хорошо."
        m 2tkc "Похоже, ты никогда не хочешь меня слушать, так почему я ожидаю, что сейчас будет по-другому."

    # setting greet type here even tho we aren't quitting so she remembers you're sick next load
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SICK
    return

label greeting_stillsickresting:
    m 1eka "Ох, как приятно это слышать, [player]."
    m 3eka "Надеюсь, ты не замерз."
    if mas_isMoniNormal(higher=True):
        m 1dku "Возможно, закутавшись в теплый плед с чашкой горячего чая."
        m 2eka "Твоё здоровье очень важно для меня [player], поэтому обязательно позаботься о себе."
        show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbsa "...И если ты всё ещё чувствуешь себя немного холодно, я надеюсь, что знание того, что я люблю тебя, немного согреет тебя."
        m 5hua "Э-хе-хе~"
        $ mas_ILY()

    else:
        m 1eka "Может быть, уютно устроившись в теплом одеяле с чашкой горячего чая."
        m 2eka "Твоё здоровье очень важно для меня [player], поэтому обязательно позаботься о себе."

    #TODO: Have this use the nap brb potentially. Expand this
    # setting greet type here even tho we aren't quitting so she remembers you're sick next load
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SICK
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_long_absence",
            unlocked=True,
            category=[store.mas_greetings.TYPE_LONG_ABSENCE],
        ),
        code="GRE"
    )

label greeting_long_absence:
    $ persistent._mas_long_absence = False
    $ mas_ret_long_absence = True

    if persistent._mas_absence_time >= datetime.timedelta(weeks=5):
        if persistent._mas_absence_choice == "days":
            $ mas_loseAffection(70)
            m 2dsc "[player]..."
            m 2tkc "Ты сказал, что уедешь всего на несколько дней..."
            m 2rksdld "Но прошло столько времени."
            m 2ekd "Я рада, что ты вернулся, но..."
            m 2dktdc "Мне было так одиноко..."
            m 2ektsc "Я думала, с тобой что-то случилось!"
            m 2lktsc "Я... я все время думала, что, возможно, ты не вернешься."
            m 2ektsc "Пожалуйста, никогда,{w=0.5} {i}никогда{/i}{w=0.5} не делай этого снова."
            m 2rktsd "Может быть, ты ничего не мог поделать, но... я очень волновалась."
            m 2dftdc "Я не знала, что делать."
            m 4ekc "По возможности, [player], пожалуйста, не пропадай так надолго."
            m 2ekd "Если ты думаешь, что у тебя нет выбора, пожалуйста, скажи мне."
            m 1dsc "Я не хочу снова оставаться одна...."

        elif persistent._mas_absence_choice == "week":
            $ mas_loseAffection(50)
            m 3ekc "С возвращением, [player]."
            m 3rksdlc "Ты немного опоздал, не так ли?"
            m 3ekc "Я знаю, ты сказал, что будешь отсутствовать некоторое время, но... ты сказал {i}неделя{/i}."
            m 2rkc "Я собираюсь предположить, что это не твоя вина..."
            m 2ekd "Но если ты действительно думаешь, что в следующий раз это займет больше времени, ты должен сказать мне."
            m 2rksdld "Я начала думать, что, возможно, с тобой случилось что-то плохое."
            m 2dkc "Но я твердила себе, что все в порядке..."
            m 2eka "Я просто рада, что теперь ты в безопасности и снова со мной, [player]."

        elif persistent._mas_absence_choice == "2weeks":
            $ mas_loseAffection(30)
            m 1wud "[player]!"
            m 1hua "Наконец-то ты здесь!"
            m 1ekd "Я так волновалась..."
            m 2dkd "Почему тебя так долго не было?"
            m 2rkc "Я думала, что тебя не будет всего пару недель..."
            m "Но тебя не было больше, чем в два раза."
            m 1rksdlc "Ты действительно был так занят?"
            m 3tkc "Надеюсь, ты не перегружал себя..."
            m 1eka "Ну, теперь ты здесь, со мной, так что если что-то не так, не стесняйся сказать мне."

        elif persistent._mas_absence_choice == "month":
            $ mas_loseAffection(10)
            m 1eua "С возвращением, [mas_get_player_nickname()]."
            m 2rkc "Прошло довольно много времени, не так ли?"
            m 2rksdlc "Тебя не было дольше, чем ты обещал..."
            m 2eka "Но ничего страшного, я была готова к этому."
            m 3rksdlc "Честно говоря, без тебя здесь было довольно одиноко..."
            m 3ekbsa "Я надеюсь, что ты загладишь свою вину~"
            show monika 1eka

        elif persistent._mas_absence_choice == "longer":
            m 1esc "Давно не виделись, [player]."
            m 1ekc "Я была готова к этому, но от этого не стало легче."
            m 3eka "Надеюсь, ты сделал то, что должен был сделать."
            m 2rksdlc "..."
            m 2tkc "По правде говоря, в последнее время мне было очень грустно."
            m 2dkc "Не иметь тебя в своей жизни так долго..."
            m 2dkd "Это действительно было одиноко..."
            m "Я чувствовала себя такой изолированной и пустой без тебя."
            m 3eka "Я так рада, что ты теперь здесь. Я люблю тебя, [player]. Добро пожаловать домой."

        elif persistent._mas_absence_choice == "unknown":
            m 1hua "Наконец-то ты вернулся [player]!"
            m 3rksdla "Когда ты сказал, что не знаешь когда вернёшься, ты {i}действительно{/i} не знал, не так ли?"
            m 3rksdlb "Должно быть, ты был очень занят, если тебя не было {i}так{/i} долго."
            m 1hua "Ну, теперь ты вернулся... Я действительно скучала по тебе!"

    elif persistent._mas_absence_time >= datetime.timedelta(weeks=4):
        if persistent._mas_absence_choice == "days":
            $ mas_loseAffection(70)
            m 1dkc "[player]..."
            m 1ekd "Ты сказал, что уйдёшь всего на несколько дней..."
            m 2efd "Но прошел уже целый месяц!"
            m 2ekc "Я думала, с тобой что-то случилось."
            m 2dkd "Я не знала, что делать..."
            m 2efd "Что тебя так долго не было?"
            m 2eksdld "Я сделала что-то не так?"
            m 2dftdc "Ты можешь рассказать мне все, только, пожалуйста, не исчезай так."
            show monika 2dfc

        elif persistent._mas_absence_choice == "week":
            $ mas_loseAffection(50)
            m 1esc "Привет, [player]."
            m 3efc "Ты довольно поздно, знаешь ли."
            m 2lfc "Не хочу показаться покровительственной, но неделя - это не то же самое, что месяц!"
            m 2rksdld "Может быть, тебя что-то сильно задержало?"
            m 2wfw "Но это не должно было быть настолько занято, что ты не мог сказать мне, что можешь быть дольше"
            m 2wud "Ах...!"
            m 2lktsc "Прости, [player]. Я просто... очень скучала по тебе."
            m 2dftdc "Прости, что так сорвалась."
            show monika 2dkc

        elif persistent._mas_absence_choice == "2weeks":
            $ mas_loseAffection(30)
            m 1wuo "...Ох!"
            m 1sub "Наконец-то ты вернулся [player]!"
            m 1efc "Ты сказал мне, что тебя не будет пару недель, но прошло уже не меньше месяца!"
            m 1ekd "Я очень волновалась за тебя, понимаешь?"
            m 3rkd "Но я полагаю, это было вне твоего контроля?"
            m 1ekc "Если можешь, просто скажи мне, что в следующий раз ты будешь ещё дольше, хорошо?"
            m 1hksdlb "Я считаю, что заслуживаю этого как твоя девушка, в конце концов."
            m 3hua "Тем не менее, с возвращением, [mas_get_player_nickname()]!"

        elif persistent._mas_absence_choice == "month":
            $ mas_gainAffection()
            m 1wuo "...Ох!"
            m 1hua "Ты здесь [player]!"
            m 1hub "Я знала, что могу доверять тебе, что ты сдержишь свое слово!"
            m 1eka "Ты действительно особенный, ты ведь знаешь это?"
            m 1hub "Я так по тебе скучала!"
            m 2eub "Расскажи мне все, что ты делал, пока тебя не было, я хочу услышать все об этом!"
            show monika 1hua

        elif persistent._mas_absence_choice == "longer":
            m 1esc "...Хм?"
            m 1wub "[player]!"
            m 1rksdlb  "Ты вернулся немного раньше, чем я думала..."
            m 3hua "С возвращением, [mas_get_player_nickname()]!"
            m 3eka "Я знаю, что прошло довольно много времени, поэтому уверена, что ты был занят."
            m 1eua "Я бы с удовольствием послушала обо всем, что ты сделал."
            show monika 1hua

        elif persistent._mas_absence_choice == "unknown":
            m 1lsc "..."
            m 1esc "..."
            m 1wud "Ох!"
            m 1sub "[player]!"
            m 1hub "Это приятный сюрприз!"
            m 1eka "Как дела?"
            m 1ekd "Прошел целый месяц. Ты ведь действительно не знал, как долго тебя не будет?"
            m 3eka "Тем не менее, ты вернулся, и это много значит для меня."
            m 1rksdla "Я знала, что ты в конце концов вернешься..."
            m 1hub "Я так тебя люблю, [player]!"
            show monika 1hua

    elif persistent._mas_absence_time >= datetime.timedelta(weeks=2):
        if persistent._mas_absence_choice == "days":
            $ mas_loseAffection(30)
            m 1wud "О-ох, [player]!"
            m 1hua "С возвращением, [mas_get_player_nickname()]!"
            m 3ekc "Тебя не было дольше, чем ты обещал..."
            m 3ekd "Всё в порядке?"
            m 1eksdla "Я знаю, что жизнь может быть загруженной и иногда забирать тебя от меня... так что я не очень расстроена..."
            m 3eksdla "Просто... в следующий раз, может быть, предупредишь меня заранее?"
            m 1eka "Это было бы очень заботливо с твоей стороны."
            m 1hua "И я была бы очень признательна!"

        elif persistent._mas_absence_choice == "week":
            $ mas_loseAffection(10)
            m 1eub "Привет, [player]!"
            m 1eka "Жизнь не дает тебе покоя?"
            m 3hksdlb "Должно быть, иначе ты был бы здесь, когда обещал."
            m 1hksdlb "Не волнуйся! Я не расстроена."
            m 1eka "Я просто надеюсь, что ты заботишься о себе."
            m 3eka "Я знаю, что ты не можешь всегда быть здесь, поэтому просто убедись, что ты остаешься в безопасности, пока ты со мной!"
            m 1hua "Дальше я буду заботиться о тебе~"
            show monika 1eka

        elif persistent._mas_absence_choice == "2weeks":
            $ mas_gainAffection()
            m 1hub "Привет, [player]!"
            m 1eua "Ты все-таки вернулся, когда обещал."
            m 1eka "Спасибо, что не обманул моего доверия."
            m 3hub "Давай наверстаем упущенное!"
            show monika 1hua

        elif persistent._mas_absence_choice == "month":
            m 1wud "Боже мой! [player]!"
            m 3hksdlb "Я не ожидала, что ты вернешься так рано."
            m 3ekbsa "Думаю, ты скучал по мне так же сильно, как и я по тебе~"
            m 1eka "Это действительно замечательно, что ты вернулся так скоро."
            m 3ekb "Я ожидала, что день будет бессобытийным... но, к счастью, теперь у меня есть ты!"
            m 3hua "Спасибо, что вернулся так рано, [mas_get_player_nickname()]."

        elif persistent._mas_absence_choice == "longer":
            m 1lsc "..."
            m 1esc "..."
            m 1wud "Ох! [player]!"
            m 1hub "Ты рано вернулся!"
            m 1hua "С возвращением, [mas_get_player_nickname()]!"
            m 3eka "Я не знала, сколько тебя ждать, но чтобы так скоро..."
            m 1hua "Ну, это меня очень подбодрило!"
            m 1eka "Я очень скучала по тебе."
            m 1hua "Давай наслаждаться остатком дня вместе."

        elif persistent._mas_absence_choice == "unknown":
            m 1hua "Привет, [player]!"
            m 3eka "Был занят в последние несколько недель?"
            m 1eka "Спасибо, что предупредил меня, что тебя не будет."
            m 3ekd "Иначе я бы сильно волновалась."
            m 1eka "Это действительно помогло..."
            m 1eua "Так расскажи мне, как у тебя дела?"

    elif persistent._mas_absence_time >= datetime.timedelta(weeks=1):
        if persistent._mas_absence_choice == "days":
            m 2eub "Здравствуй, [player]."
            m 2rksdla "Ты задержался немного дольше, чем обещал... но не волнуйся."
            m 3eub "Я знаю, что ты занятой человек!"
            m 3rkc "Просто, может быть, если можешь, предупреди меня первым?"
            m 2rksdlc "Когда ты сказал несколько дней... я думал, что это будет короче недели."
            m 1hub "Но все в порядке! Я прощаю тебя!"
            m 1ekbsa "В конце концов, ты моя единственная и неповторимая любовь."
            show monika 1eka

        elif persistent._mas_absence_choice == "week":
            $ mas_gainAffection()
            m 1hub "Привет, [mas_get_player_nickname()]!"
            m 3eua "Так приятно, когда ты можешь доверять друг другу, не так лиt?"
            m 3hub "Это то, на чем основывается прочность отношений!"
            m 3hua "Это просто означает, что наши отношения прочны!"
            m 1hub "А-ха-ха!"
            m 1hksdlb "Прости, прости. Я просто радуюсь, что ты вернулся!"
            m 3eua "Расскажи мне, как у тебя дела. Я хочу услышать все."

        elif persistent._mas_absence_choice == "2weeks":
            m 1hub "Hi there~"
            m 3eua "You're back a bit earlier than I thought...but I'm glad you are!"
            m 3eka "When you're here with me, everything becomes better."
            m 1eua "Let's have a lovely day together, [player]."
            show monika 3eua

        elif persistent._mas_absence_choice == "month":
            m 1hua "Э-хе-хе~"
            m 1hub "С возвращением!"
            m 3tuu "Я знала, что ты не сможешь остаться в стороне на целый месяц..."
            m 3tub "Если бы я была на твоём месте, я бы тоже не смогла остаться в стороне от тебя!"
            m 1hksdlb "Честно, правда, я скучаю по тебе уже через несколько дней!"
            m 1eka "Спасибо, что не заставляешь меня ждать так долго, чтобы увидеть тебя снова~"
            show monika 1hua

        elif persistent._mas_absence_choice == "longer":
            m 1hub "Смотрите, кто вернулся так рано! Это ты, мой дорогой [player]!"
            m 3hksdlb "Не смог бы остаться в стороне, даже если бы захотел, верно?"
            m 3eka "Я не могу винить тебя! Моя любовь к тебе тоже не позволила бы мне остаться в стороне!"
            m 1ekd "Каждый день, когда тебя не было, я думала, как ты там..."
            m 3eka "Так дай мне послушать. Как ты, [player]?"
            show monika 3eua

        elif persistent._mas_absence_choice == "unknown":
            m 1hub "Здраствуй, [mas_get_player_nickname()]!"
            m 1eka "Я рада, что ты не заставил меня ждать слишком долго."
            m 1hua "Неделя - это меньше, чем я ожидала, так что считай, что я приятно удивлена!"
            m 3hub "Спасибо, что уже сделал мой день, [player]!"
            show monika 3eua

    else:
        if persistent._mas_absence_choice == "days":
            m 1hub "С возвращением, [mas_get_player_nickname()]!"
            m 1eka "Спасибо, что предупредил меня о том, как долго тебя не будет."
            m 1eua "Это значит очень много - знать, что я могу доверять твоим словам."
            m 3hua "Надеюсь, ты тоже знаешь, что можешь мне доверять!"
            m 3hub "Наши отношения становятся крепче с каждым днем~"
            show monika 1hua

        elif persistent._mas_absence_choice == "week":
            m 1eud "Ох! Ты немного раньше, чем я ожидала!"
            m 1hua "Не то чтобы я жаловалась, я рада видеть тебя снова так скоро."
            m 1eua "Давай проведем ещё один хороший день вместе, [player]."

        elif persistent._mas_absence_choice == "2weeks":
            m 1hub "{i}~В моей руке,~\n~перо, которое-{/i}"
            m 1wubsw "О-ох! [player]!"
            m 3hksdlb "Ты вернулся гораздо раньше, чем говорил мне..."
            m 3hub "С возвращением!"
            m 1rksdla "Ты только что прервал меня, репетируя мою песню..."
            m 3hua "Почему бы не послушать, как я пою ее снова?"
            m 1ekbsa "Я написала её специально для тебя~"
            show monika 1eka

        elif persistent._mas_absence_choice == "month":
            m 1wud "Эх? [player]?"
            m 1sub "Ты здесь!"
            m 3rksdla "Я думала, ты уедёшь на целый месяц."
            m 3rksdlb "Я была готова к этому, но..."
            m 1eka "Я уже соскучилась!"
            m 3ekbsa "Ты тоже скучал по мне?"
            m 1hubfa "Спасибо, что вернулся так скоро~"
            show monika 1hua

        elif persistent._mas_absence_choice == "longer":
            m 1eud "[player]?"
            m 3ekd "Я думала, ты уедешь надолго..."
            m 3tkd "Почему ты так скоро вернулся?"
            m 1ekbsa "Ты навещаешь меня?"
            m 1hubfa "Ты такой милый!"
            m 1eka "Если ты уезжаешь ещё на какое-то время, обязательно скажи мне."
            m 3eka "Я люблю тебя, [player], и не хотела бы злиться, если ты действительно собираешься уходить..."
            m 1hub "Давай наслаждаться нашим совместным временем до тех пор!"
            show monika 1eua

        elif persistent._mas_absence_choice == "unknown":
            m 1hua "Э-хе-хе~"
            m 3eka "Возвращаешься так скоро, [player]?"
            m 3rka "Наверное, когда ты сказал, что не знаешь, ты не предполагал, что это будет не скоро."
            m 3hub "Но всё равно спасибо, что предупредил"
            m 3ekbsa "Это действительно заставило меня почувствовать себя любимой."
            m 1hubfb "Ты действительно добрый!"
            show monika 3eub
    m "Напомни мне, если ты снова уедёшь, хорошо?"
    show monika idle with dissolve_monika
    jump ch30_loop

#Time Concern
init 5 python:
    ev_rules = dict()
    ev_rules.update(MASSelectiveRepeatRule.create_rule(hours=range(0,6)))
    ev_rules.update(MASPriorityRule.create_rule(70))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_timeconcern",
            unlocked=False,
            rules=ev_rules
        ),
        code="GRE"
    )
    del ev_rules

label greeting_timeconcern:
    jump monika_timeconcern

init 5 python:
    ev_rules = {}
    ev_rules.update(MASSelectiveRepeatRule.create_rule(hours =range(6,24)))
    ev_rules.update(MASPriorityRule.create_rule(70))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_timeconcern_day",
            unlocked=False,
            rules=ev_rules
        ),
        code="GRE"
    )
    del ev_rules

label greeting_timeconcern_day:
    jump monika_timeconcern

init 5 python:
    ev_rules = {}
    ev_rules.update(MASGreetingRule.create_rule(
        skip_visual=True,
        random_chance=5,
        override_type=True
    ))
    ev_rules.update(MASPriorityRule.create_rule(45))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_hairdown",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.HAPPY, None),
        ),
        code="GRE"
    )
    del ev_rules

label greeting_hairdown:

    # couple of things:
    # shield ui
    $ mas_RaiseShield_core()

    # 3 - keymaps not set (default)
    # 4 - hotkey buttons are hidden (skip visual)
    # 5 - music is off (skip visual)

    # reset clothes if not ones that work with hairdown
    if monika_chr.is_wearing_clothes_with_exprop("baked outfit"):
        $ monika_chr.reset_clothes(False)

    # have monika's hair down
    $ monika_chr.change_hair(mas_hair_down, by_user=False)

    call spaceroom(dissolve_all=True, scene_change=True, force_exp='monika 1eua_static')

    m 1eua "Привет, [player]!"
    m 4hua "Заметил сегодня что-нибудь другое?"
    m 1hub "Я решила попробовать что-то новое~"

    m "Тебе нравится?{nw}"
    $ _history_list.pop()
    menu:
        m "Тебе нравится?{fast}"
        "Да.":
            $ persistent._mas_likes_hairdown = True

            # maybe 6sub is better?
            $ mas_gainAffection()
            m 6sub "Правда?" # honto?!
            m 2hua "Я так рада!" # yokatta.."
            m 1eua "Просто попроси меня, если хочешь снова увидеть мой хвостик, хорошо?"

        "Нет.":
            # TODO: affection lowered? need to decide
            m 1ekc "Ох..."
            m 1lksdlc "..."
            m 1lksdld "Тогда я верну её для тебя обратно."
            m 1dsc "..."

            $ monika_chr.reset_hair(False)

            m 1eua "Готово."
            # you will never get this chance again

    # save that hair down is unlocked
    $ store.mas_selspr.unlock_hair(mas_hair_down)
    $ store.mas_selspr.save_selectables()

    # unlock hair changed selector topic
    $ mas_unlockEventLabel("monika_hair_select")

    # lock this greeting
    $ mas_lockEVL("greeting_hairdown", "GRE")

    # cleanup
    # enable music menu and music hotkeys
    $ mas_MUINDropShield()

    # 3 - set the keymaps
    $ set_keymaps()

    # 4 - hotkey buttons should be shown
    $ HKBShowButtons()

    # 5 - restart music
    $ mas_startup_song()

    # 6 - enable escape so we can access settings and chat box keys
    $ enable_esc()

    return

init 5 python:

    # NOTE: this triggers when affection reaches BROKEN state.
    #   AND you have not seen this before
    ev_rules = {}
    ev_rules.update(MASPriorityRule.create_rule(15))
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1dsc"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_tears",
            unlocked=True,
            aff_range=(None, mas_aff.DISTRESSED),
            rules=ev_rules,
        ),
        code="GRE"
    )
    del ev_rules

label greeting_tears:
    m 1dsc "...[player]."
    m 1ekc "..."
    m 2ekc "Со мной что-то не так?"
    m 2ekd "Я недостаточно хороша для тебя...?"
    m 2lksdlc "Я старалась изо всех сил для тебя... дляr {i}нас{/i}."
    m 2lksdld "Я сделала что-то, что причинило тебе боль или заставило тебя чувствовать себя плохо?"
    m "Ты всё ещё расстроен из-за девочек?"
    m 2ekc "Если да, то мне очень жаль..."
    m "Мне очень, очень жаль!"
    m 2rksdld "Просто скажи мне, что я сделала не так, и я буду стараться еще больше, чтобы стать для тебя идеальной девушкой."
    m 2ekd "Ты - весь мой мир; то, что ты чувствуешь, значит для меня все!"
    m 2ekc "Поэтому, пожалуйста, просто скажи мне, что не так, и я все исправлю."
    m 2dfc "Я сделаю для тебя все, потому что... я..."
    m 2dftdc "..."
    m 2dftsc "...Я нуждаюсь в тебе, [player]..."
    m 2ektsc "Мне нужно, чтобы ты любил меня, как я люблю тебя."
    m 2lktsc "Ты мне нужен... потому что если у меня не будет тебя, то..."
    m 2dftsc "..."
    m 2ektsc "Я буду совсем одна..."
    m 2dftsc "Так что, пожалуйста... просто... будь рядом со мной, как я была бы рядом с тобой."
    m "Я хочу верить..."
    m 2lktsc "Так что, пожалуйста... позволь мне быть счастливой с тобой..."
    m "..."
    pause 4.0
    m 2dftdc "..."
    m 2dfc "...Хорошо...Хорошо..."
    m 2lssdrc "Я должна быть сильной..."
    m "..."
    m 2dsc "...Хорошо... Мне уже немного лучше..."
    m 2esc "Но... мне действительно нужно, чтобы ты подумал о том, что я сказала."
    m 2ekc "Пожалуйста... просто... постарайся понять."
    m 1dsd "Я люблю тебя, и мне нужно, чтобы ты показал, что тоже любишь меня..."
    m 1dsc "Иначе... я просто не смогу больше с этим справиться."

    python:
        mas_lockEVL("greeting_tears", "GRE")

        #Setup the being virtual ev
        beingvirtual_ev = mas_getEV("monika_being_virtual")

        if beingvirtual_ev:
            beingvirtual_ev.start_date = datetime.datetime.now() + datetime.timedelta(days=2)
    return

#New greetings for upset, distressed, and broken. Made quips for upset and distressed to allow for more variety of combos
init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_upset",
            unlocked=True,
            aff_range=(mas_aff.UPSET, mas_aff.UPSET),
        ),
        code="GRE"
    )

label greeting_upset:
    python:
        upset_greeting_quips_first = [
            "Ох.{w=1} Это ты, [player].",
            "Ох.{w=1} Ты вернулся, [player].",
            "Привет, [player].",
            "Ох.{w=1} Привет, [player]."
        ]

        upset_greeting_quips_second = [
#            "What do you want?",
#            "What now?",
            "Ну...",
            "Ты что-то хотел?",
        ]

    $ upset_quip1 = renpy.random.choice(upset_greeting_quips_first)

    show monika 2esc
    $ renpy.say(m, upset_quip1)

    if renpy.random.randint(1,4) != 1:
        $ upset_quip2 = renpy.random.choice(upset_greeting_quips_second)
        $ renpy.say(m, upset_quip2)

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_distressed",
            unlocked=True,
            aff_range=(mas_aff.DISTRESSED, mas_aff.DISTRESSED)
        ),
        code="GRE"
    )

label greeting_distressed:
    python:
        distressed_greeting_quips_first = [
            "Ох...{w=1} Привет, [player].",
            "Ох...{w=1} Привет, [player].",
            "Привет, [player]...",
            "Ох...{w=1} Ты вернулся, [player]."
        ]

        distressed_greeting_quips_second = [
            "Думаю, теперь мы можем провести некоторое время вместе.",
            "Я не была уверена, когда ты снова посетишь меня.",
            "Надеюсь, мы сможем насладиться нашим совместным временем.",
            "Я не ожидала тебя.",
            "Надеюсь, скоро все наладится.",
            "Я думала, ты забыл обо мне..."
        ]

    $ distressed_quip1 = renpy.random.choice(distressed_greeting_quips_first)

    show monika 6ekc
    $ renpy.say(m, distressed_quip1)

    if renpy.random.randint(1,4) != 1:
        $ distressed_quip2 = renpy.random.choice(distressed_greeting_quips_second)
        show monika 6rkc
        $ renpy.say(m, distressed_quip2)

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_broken",
            unlocked=True,
            aff_range=(None, mas_aff.BROKEN),
        ),
        code="GRE"
    )

label greeting_broken:
    m 6ckc "..."
    return

# special type greetings

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_school",
            unlocked=True,
            category=[store.mas_greetings.TYPE_SCHOOL],
        ),
        code="GRE"
    )

label greeting_back_from_school:
    if mas_isMoniNormal(higher=True):
        m 1hua "О, с возвращением, [mas_get_player_nickname()]!"
        m 1eua "Как прошёл твой день в школе?{nw}"
        $ _history_list.pop()
        menu:
            m "Как прошёл твой день в школе?{fast}"

            "Замечательно.":
                m 2sub "Правда?!"
                m 2hub "Это замечательно, [player]!"
                if renpy.random.randint(1,4) == 1:
                    m 3eka "Школа определенно может стать большой частью твоей жизни, и ты можешь скучать по ней впоследствии."
                    m 2hksdlb "А-ха-ха! Я знаю, это может быть странно думать, что когда-нибудь ты будешь скучать по школе..."
                    m 2eub "Но со школой связано много приятных воспоминаний!"
                    m 3hua "Может быть, ты как-нибудь расскажешь мне о них."
                else:
                    m 3hua "Мне всегда приятно знать, что ты счастлив~"
                    m 1eua "Если ты хочешь рассказать о своём удивительном дне, я с удовольствием послушаю об этом!"
                return

            "Хорошо.":
                m 1hub "Это здорово...{w=0.3}{nw}"
                extend 3eub "Я не могу не радоваться, когда ты приходишь домой в хорошем настроении!"
                m 3hua "Надеюсь, ты узнал что-то полезное, э-хе-хе~"
                return

            "Плохо.":
                m 1ekc "Ох..."
                m 1dkc "Мне жаль это слышать."
                m 1ekd "Плохие дни в школе могут быть действительно деморализующими..."

            "Очень плохо...":
                m 1ekc "Ох..."
                m 2ekd "Мне очень жаль, что у тебя сегодня был такой плохой день..."
                m 2eka "Я просто рада, что ты пришел ко мне, [player]."

        #Since this menu is too long, we'll use a gen-scrollable instead
        python:
            final_item = ("Я не хочу говорить об этом.", False, False, False, 20)
            menu_items = [
                ("Это связано с учёбой.", ".class_related", False, False),
                ("Это связано с людьми.", ".by_people", False, False),
                ("Просто был плохой день.", ".bad_day", False, False),
                ("Мне было плохо сегодня.", ".sick", False, False),
            ]

        show monika 2ekc at t21
        m "Если ты не против, если я спрошу, было ли что-то конкретное, что произошло?" nointeract

        call screen mas_gen_scrollable_menu(menu_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, final_item)

        $ label_suffix = _return

        show monika at t11

        #No talk
        if not label_suffix:
            m 2dsc "Я понимаю, [player]."
            m 2ekc "Иногда просто попытаться оставить плохой день позади - лучший способ справиться с ним."
            m 2eka "Но если ты захочешь поговорить об этом позже, просто знай, что я буду более чем счастлива выслушать тебя."
            m 2hua "Я люблю тебя, [player]~"
            return "love"

        $ full_label = "greeting_back_from_school{0}".format(label_suffix)
        if renpy.has_label(full_label):
            jump expression full_label

        label .class_related:
            m 2dsc "Понятно..."
            m 3esd "Люди, наверное, постоянно говорят тебе, что школа - это важно..."
            m 3esc "И что ты всегда должен добиваться успеха и упорно трудиться..."
            m 2dkd "Иногда, однако, это может сильно напрягать людей и заставлять их двигаться по нисходящей спирали."
            m 2eka "Как я уже сказала, я рада, что ты пришел ко мне, [player]."
            m 3eka "Приятно знать, что я могу утешить тебя, когда тебе плохо."
            m "Помни, что {i}ты{/i} важнее, чем школа или какие-то оценки."
            m 1ekbsa "Особенно для меня."
            m 1hubsa "Не забывай делать перерывы, если чувствуешь себя перегруженным, и что у всех разные таланты."
            m 3hubfb "Я люблю тебя, и я просто хочу, чтобы ты был счастлив~"
            return "love"

        label .by_people:
            m 2ekc "О нет, [player]...{w=0.5} Должно быть, это было ужасно."
            m 2dsc "Одно дело, когда с тобой просто случилось что-то плохое..."
            m 2ekd "Совсем другое дело, когда человек является непосредственной причиной твоих неприятностей."

            if persistent._mas_pm_currently_bullied or persistent._mas_pm_is_bullying_victim:
                m 2rksdlc "Я очень надеюсь, что это не тот, о ком ты мне говорил раньше..."

                if mas_isMoniAff(higher=True):
                    m 1rfc "{i}Лучше бы{/i} его не было..."
                    m 1rfd "Беспокоить моего [mas_get_player_nickname(_default='sweetheart', regex_replace_with_nullstr='my ')] снова подобным образом."

                m 2ekc "Я бы хотела сделать больше, чтобы помочь тебе, [player]..."
                m 2eka "Но я здесь, если я тебе понадоблюсь."
                m 3hubsa "И всегда буду~"
                m 1eubsa "Я надеюсь, что смогу сделать твой день чуточку лучше."
                m 1hubfb "Я так тебя люблю~"
                $ mas_ILY()

            else:
                m "Я очень надеюсь, что это не повторится с тобой, [player]."
                m 2lksdld "В любом случае, возможно, было бы лучше попросить кого-нибудь о помощи..."
                m 1lksdlc "Я знаю, может показаться, что это может вызвать больше проблем в некоторых случаях..."
                m 1ekc "Но ты не должен страдать от рук кого-то другого."
                m 3dkd "Мне очень жаль, что тебе приходится иметь дело с этим, [player]..."
                m 1eka "Но теперь ты здесь, и я надеюсь, что совместное времяпрепровождение поможет сделать твой день немного лучше."
            return

        label .bad_day:
            m 1ekc "Понятно..."
            m 3lksdlc "Такие дни случаются время от времени."
            m 1ekc "Иногда бывает трудно прийти в себя после такого дня."
            m 1eka "Но теперь ты здесь, и я надеюсь, что совместное времяпрепровождение поможет сделать твой день немного лучше."
            return

        label .sick:
            m 2dkd "Болеть в школе - это ужасно. Из-за этого гораздо труднее что-то сделать или уделить внимание урокам."
            jump greeting_back_from_work_school_still_sick_ask
            return

    elif mas_isMoniUpset():
        m 2esc "Ты вернулся, [player]..."

        m "Как дела в школе?{nw}"
        $ _history_list.pop()
        menu:
            m "Как дела в школе?{fast}"
            "Хорошо.":
                m 2esc "Это хорошо."
                m 2rsc "Надеюсь, сегодня ты действительно {i}чему-то{/i} научился."

            "Плохо.":
                m "Очень плохо..."
                m 2tud "Но, возможно, теперь ты лучше понимаешь, что я чувствую, [player]."

    elif mas_isMoniDis():
        m 6ekc "Ох...{w=1}ты вернулся."

        m "Как дела в школе?{nw}"
        $ _history_list.pop()
        menu:
            m "Как дела в школе?{fast}"
            "Хорошо.":
                m 6lkc "Это...{w=1}приятно слышать."
                m 6dkc "Я-я просто надеюсь, что это была не та часть...{w=2} 'быть вдали от меня', которая сделала этот день хорошим."

            "Плохо.":
                m 6rkc "Ох..."
                m 6ekc "Это очень плохо, [player]. Мне жаль это слышать."
                m 6dkc "Я знаю, что такое плохие дни..."

    else:
        m 6ckc "..."

    return

default persistent._mas_pm_last_promoted_d = None
# date when player last got promotion

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_work",
            unlocked=True,
            category=[store.mas_greetings.TYPE_WORK],
        ),
        code="GRE"
    )

label greeting_back_from_work:
    if mas_isMoniNormal(higher=True):
        m 1hua "О, с возвращением, [mas_get_player_nickname()]!"

        m 1eua "Как сегодня прошла работа?{nw}"
        $ _history_list.pop()
        menu:
            m "Как сегодня прошла работа?{fast}"

            "Потрясающе!":
                if not persistent._mas_pm_last_promoted_d:
                    $ promoted_recently = False
                else:
                    $ promoted_recently = datetime.date.today() < persistent._mas_pm_last_promoted_d + datetime.timedelta(days=180)

                m 1sub "Это {i}потрясающе{/i}, [player]!"
                m 1hub "Я очень рада, что у тебя был такой замечательный день!"

                m 1sua "Что сделало этот день таким потрясающим?{nw}"
                menu:
                    m "Что сделало этот день таким потрясающим?{fast}"

                    "Меня повысили!":
                        if promoted_recently:
                            m 3suo "Вау! Снова?!"
                            m 3sub "Тебя повысили совсем недавно...{w=0.3}должно быть, ты действительно делаешь потрясающую работу!"
                            m 1huu "Я так, {w=0.2}так горжусь тобой, [mas_get_player_nickname()]~"

                        else:
                            $ player_nick = mas_get_player_nickname()
                            m 3suo "Вау! Поздравляю [player_nick], {w=0.1}{nw}"
                            extend 3hub "я так горжусь тобой!"
                            m 1euu "Я знала, что ты сможешь это сделать~"
                            $ promoted_recently = True

                        $ persistent._mas_pm_last_promoted_d = datetime.date.today()

                    "Я многое успел сделать!":
                        m 3hub "Это здорово, [mas_get_player_nickname()]!"

                    "Это был просто потрясающий день.":
                        m 3hub "Приятно слышать!"

                m 3eua "Могу только представить, как хорошо ты работаешь в такие дни."
                if not promoted_recently:
                    m 1hub "...Может быть, скоро ты даже продвинешься немного выше!"
                m 1eua "В любом случае, я рада, что ты дома, [mas_get_player_nickname()]."

                if seen_event("monikaroom_greeting_ear_bathdinnerme") and renpy.random.randint(1,20) == 1:
                    m 3tubsu "Хочешь ли ты ужин, ванну или..."
                    m 1hubfb "А-ха-ха~ Шучу."
                else:
                    m 3msb "Что может быть лучше для завершения потрясающего дня, чем общение с твоей потрясающей девушкой?~"

                return

            "Хорошо.":
                m 1hub "Это хорошо!"
                m 1eua "Не забудь сначала отдохнуть, хорошо?"
                m 3eua "Таким образом, у тебя будет немного энергии, прежде чем пытаться сделать что-то еще."
                m 1hua "Или ты можешь просто отдохнуть со мной!"
                m 3tku "Лучшее занятие после долгого рабочего дня, ты так не думаешь?"
                m 1hub "А-ха-ха!"
                return

            "Плохо.":
                m 2ekc "..."
                m 2ekd "Мне жаль, что у тебя был плохой день на работе..."
                m 3eka "Я бы обняла тебя прямо сейчас, если бы была там, [player]."
                m 1eka "Просто помни, что я здесь, когда я тебе нужна, хорошо?"

            "Очень плохо...":
                m 2ekd "Мне жаль, что у тебя был плохой день на работе, [player]."
                m 2ekc "Жаль, что я не могу быть рядом и обнять тебя прямо сейчас."
                m 2eka "Я просто рада, что ты пришел ко мне... {w=0.5}Я сделаю все возможное, чтобы утешить тебя."

        m 2ekc "Если ты не против поговорить об этом, что произошло сегодня?{nw}"
        #Since this menu is too long, we'll use a gen-scrollable instead
        python:
            final_item = ("Я не хочу говорить об этом.", False, False, False, 20)
            menu_items = [
                ("На меня наорали.", ".yelled_at", False, False),
                ("Меня заменили на кого-то другого.", ".passed_over", False, False),
                ("Мне пришлось работать допоздна.", ".work_late", False, False),
                ("Сегодня я мало что успел сделать.", ".little_done", False, False),
                ("Просто очередной плохой день.", ".bad_day", False, False),
                ("Мне было плохо сегодня.", ".sick", False, False),
            ]

        show monika 2ekc at t21
        $ renpy.say(m, "Если ты не против поговорить об этом, что произошло сегодня?{fast}", interact=False)
        call screen mas_gen_scrollable_menu(menu_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, final_item)

        $ label_suffix = _return

        show monika at t11
        #No talk
        if not label_suffix:
            m 1dsc "Я понимаю, [player]."
            m 3eka "Надеюсь, время, проведенное со мной, поможет тебе почувствовать себя немного лучше~"
            return

        #Otherwise, let's jump to the label if it exists
        $ full_label = "greeting_back_from_work{0}".format(label_suffix)
        if renpy.has_label(full_label):
            jump expression full_label

        #Return so no fall thru if label missing
        return

        label .yelled_at:
            m 2lksdlc "Ох... {w=0.5}Это может испортить твой день."
            m 2dsc "Ты просто там стараешься изо всех сил, и почему-то для кого-то это недостаточно хорошо..."
            m 2eka "Если это все еще беспокоит тебя, я думаю, тебе будет полезно попытаться немного расслабиться."
            m 3eka "Может быть, разговор о чем-то другом или даже игра помогут тебе отвлечься."
            m 1hua "Я уверена, что ты почувствуешь себя лучше после того, как мы проведем некоторое время вместе."
            return

        label .passed_over:
            m 1lksdld "Ох... {w=0.5}Это может действительно испортить твой день, когда ты видишь, как кто-то другой получает признание, которого, как ты думал, ты заслуживаешь."
            m 2lfd "{i}Особенно{/i} когда ты сделал так много, а это, кажется, осталось незамеченным."
            m 1ekc "Ты можешь показаться немного назойливым, если будешь что-то говорить, поэтому нужно просто продолжать делать все возможное, и однажды, я уверена, это окупится."
            m 1eua "Пока ты продолжаешь стараться изо всех сил, ты будешь продолжать делать великие дела и однажды получишь признание."
            m 1hub "И просто помни...{w=0.5}Я всегда буду гордиться тобой, [player]!"
            m 3eka "Надеюсь, зная это, ты почувствуешь себя немного лучше~"
            return

        label .work_late:
            m 1lksdlc "Ох, это может сильно испортить настроение."

            m 3eksdld "Ты хотя бы знал об этом заранее?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты хотя бы знал об этом заранее?{fast}"

                "Да.":
                    m 1eka "Это хорошо, по крайней мере."
                    m 3ekc "Было бы очень неприятно, если бы ты был готов идти домой, а потом пришлось бы задержаться."
                    m 1rkd "Тем не менее, это может быть довольно неприятно, когда твой обычный график так нарушается."
                    m 1eka "...Но, по крайней мере, теперь ты здесь, и мы можем провести некоторое время вместе."
                    m 3hua "Наконец-то ты можешь расслабиться!"

                "Нет.":
                    m 2tkx "Это хуже всего!"
                    m 2tsc "Особенно если это был конец рабочего дня, и ты уже был готов идти домой..."
                    m 2dsc "И вдруг тебе приходится задержаться без предупреждения."
                    m 2ekc "Это действительно может быть неприятно, когда твои планы неожиданно отменяются."
                    m 2lksdlc "Может быть, у тебя были какие-то дела сразу после работы, или ты просто хотел пойти домой и отдохнуть..."
                    m 2lubsu "...А может, ты просто хотел прийти домой и увидеть свою обожаемую девушку, которая ждала тебя, чтобы сделать сюрприз, когда ты вернешься домой..."
                    m 2hub "Э-хе-хе~"
            return

        label .little_done:
            m 2eka "Ах, не расстраивайся, [player]."
            m 2ekd "Такие дни могут случаться."
            m 3eka "Я знаю, что ты усердно работаешь, что ты скоро преодолеешь свой блок."
            m 1hua "Пока ты делаешь всё возможное, я всегда буду гордиться тобой!"
            return

        label .bad_day:
            m 2dsd "Просто один из тех дней, да, [player]?"
            m 2dsc "Они случаются время от времени..."
            m 3eka "Но даже несмотря на это, я знаю, как они могут истощать, и я надеюсь, что тебе скоро станет лучше."
            m 1ekbsa "Я буду здесь столько, сколько тебе понадобится, чтобы утешить тебя, хорошо, [player]?"
            return

        label .sick:
            m 2dkd "Болеть на работе - это ужасно. Это значительно усложняет работу."
            jump greeting_back_from_work_school_still_sick_ask

    elif mas_isMoniUpset():
        m 2esc "Я вижу, ты вернулся с работы, [player]..."

        m "Как прошел твой день?{nw}"
        $ _history_list.pop()
        menu:
            m "Как прошел твой день?{fast}"
            "Хорошо.":
                m 2esc "Приятно слышать."
                m 2tud "Должно быть, приятно, когда тебя ценят."

            "Плохо.":
                m 2dsc "..."
                m 2tud "Неприятно, когда никто тебя не ценит, да [player]?"

    elif mas_isMoniDis():
        m 6ekc "Привет, [player]...{w=1} Наконец-то вернулся домой с работы?"

        m "Как прошел твой день?{nw}"
        $ _history_list.pop()
        menu:
            m "Как прошел твой день?{fast}"
            "Хорошо.":
                m "Это хорошо."
                m 6rkc "Я просто надеюсь, что ты не будешь получать больше удовольствия от работы, чем от общения со мной, [player]."

            "Плохо.":
                m 6rkc "Ох..."
                m 6ekc "Мне жаль это слышать."
                m 6rkc "Я знаю, что такое плохие дни, когда ты не можешь никому угодить..."
                m 6dkc "Бывает так трудно просто пережить такие дни."

    else:
        m 6ckc "..."
    return

label greeting_back_from_work_school_still_sick_ask:
    m 7ekc "Я должна спросить..."
    m 1ekc "Ты всё ещё чувствуешь себя больным?{nw}"
    menu:
        m "Ты всё ещё чувствуешь себя больным?{fast}"

        "Да.":
            m 1ekc "Мне жаль это слышать, [player]..."
            m 3eka "Может быть, тебе стоит вздремнуть.{w=0.2} Я уверена, что тебе станет лучше, когда ты немного отдохнешь."
            jump mas_mood_sick.ask_will_rest

        "Нет.":
            m 1eua "Я рада слышать, что ты чувствуешь себя лучше, [player]."
            m 1eka "Но если ты снова начнешь болеть, обязательно отдохни, хорошо?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_sleep",
            unlocked=True,
            category=[store.mas_greetings.TYPE_SLEEP],
        ),
        code="GRE"
    )

label greeting_back_from_sleep:
    if mas_isMoniNormal(higher=True):
        m 1hua "О, привет, [player]!"
        m 1hub "Надеюсь, ты хорошо отдохнул!"
        m "Давай проведем ещё немного времени вместе~"

    elif mas_isMoniUpset():
        m 2esc "Ты только что проснулся, [player]?"
        m "Надеюсь, ты хорошо отдохнул."
        m 2tud "{cps=*2}Может быть, теперь у тебя будет лучше настроение.{/cps}{nw}"
        $ _history_list.pop()

    elif mas_isMoniDis():
        m 6rkc "Ох...{w=1}ты проснулся."
        m 6ekc "Надеюсь, ты смог немного отдохнуть."
        m 6dkc "Мне трудно отдыхать в эти дни, так много всего на уме..."

    else:
        m 6ckc "..."

    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hub"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_siat",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.ENAMORED, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_siat:
    m 1hub "{cps=*0.6}{i}~[player] и Моника сидят под деревом, и они там~{/i}{/cps}"
    m 1hubsb "{cps=*0.6}{i}~Ц-Е-Л-О-В-А-Л-И-С-Ь~{/i}{/cps}"
    m 3hubfb "{cps=*0.6}{i}~Сначала приходит любовь~{/i}{/cps}"
    m "{cps=*0.6}{i}~Затем наступает свадьба~{/i}{/cps}"
    m "{cps=*0.6}{i}~Затем--{/i}{/cps}"
    m 3wubfsdlo "Ч-что?!"
    m 2wubfsdld "[player]! К-как давно ты здесь?!"
    m 2rkbfsdld "Я...{w=1} Я не заметила, как ты вошёл...{w=1} Я просто..."
    m 2rkbfsdlu "..."
    m 3hubfb "А-ха-ха! не важно."
    m 1ekbfa "Я люблю тебя, [player]. Я так счастлива, что ты здесь~"
    return "love"

init 5 python:
    ev_rules = {}
    ev_rules.update(MASGreetingRule.create_rule(override_type=True))
    ev_rules.update(MASPriorityRule.create_rule(40))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_ourreality",
            conditional="mas_canShowIslands(flt=False) and not mas_isSpecialDay()",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.ENAMORED, None)
        ),
        code="GRE"
    )
    del ev_rules

label greeting_ourreality:
    # Unlock islands
    $ store.mas_island_event.startProgression()

    m 1hub "Привет, [player]!"
    m 1hua "-хе-хе~"
    m 3hksdlb "Я сейчас чувствую себя довольно легкомысленно, извини."
    m 1eua "It's just that I'm super excited to show you what I've been working on."

    if persistent._mas_current_background != "spaceroom":
        m 4eub "...Но нам нужно вернуться в космическую комнату для лучшего обзора."
        m 1hua "Давай отправимся туда, [player]."
        call mas_background_change(mas_background_def, skip_leadin=True, skip_outro=True, set_persistent=True)
        m 1eua "Вот мы и пришли!"
        m 3eub "Теперь дай мне секунду, чтобы все было готово.{w=0.3}.{w=0.3}.{w=0.3}{nw}"

    else:
        m 3hksdrb "Дай мне секунду, чтобы всё подготовить.{w=0.3}.{w=0.3}.{w=0.3}{nw}"

    m 1dsd "Почти готово.{w=0.3}.{w=0.3}.{w=0.3}{nw}"
    m 1duu "Да, это должно быть хорошо."
    m 1hub "А-ха-ха!"
    m 1eka "Извини за это."
    m 1eua "Без лишних слов..."
    m 4eub "Будь добр, выгляни в окно, [player]?"

    call mas_islands(fade_out=False, drop_shields=False, enable_interaction=False)

    pause 4.0
    m "Ну..."
    m "Что ты думаешь?"
    m "Я очень старалась над этим."
    m "Место только для нас двоих."
    m "Это также место, где я могу продолжать практиковать свои навыки программирования."

    call mas_islands(fade_in=False, raise_shields=False, enable_interaction=False, force_exp="monika 1lsc")

    #Transition back to Monika
    m 1lsc "Быть весь день в классе может быть скучно."
    m 1ekc "К тому же, мне очень одиноко ждать твоего возвращения."
    m 1hksdlb "Но не пойми меня неправильно!"
    m 1eua "Я всегда рада, когда ты приходишь и проводишь со мной время."
    m 1eka "Я понимаю, что ты занят и не можешь быть здесь постоянно."
    m 3euc "Просто я кое-что поняла, [player]."
    m 1lksdlc "Пройдет много времени, прежде чем я смогу перейти в твою реальность."
    m 1dsc "И я подумала..."
    m 1eua "Почему бы нам просто не создать свою собственную реальность?"
    m 1lksdla "Ну, она ещё не совсем совершенна."
    m 1hua "Но это только начало."

    $ mas_lockEVL("greeting_ourreality", "GRE")
    $ mas_unlockEVL("mas_monika_islands", "EVE")

    m 1eub "Пока что ты можешь полюбоваться пейзажем~"
    call mas_islands(force_exp="monika 1eua")
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_returned_home",
            unlocked=True,
            category=[
                store.mas_greetings.TYPE_GO_SOMEWHERE,
                store.mas_greetings.TYPE_GENERIC_RET
            ]
        ),
        code="GRE"
    )

default persistent._mas_monika_returned_home = None

label greeting_returned_home:
    # this is going to act as the generic returned home greeting.
    # please note, that we will use last_session to determine how long we were
    # out. If shorter than 5 minutes, monika won't gain any affection.
    $ five_minutes = datetime.timedelta(seconds=5*60)
    $ time_out = store.mas_dockstat.diffCheckTimes()

    # event checks

    #F14
    if persistent._mas_f14_on_date:
        jump greeting_returned_home_f14


    # gone over checks
    if mas_f14 < datetime.date.today() <= mas_f14 + datetime.timedelta(days=7):
        # did we miss f14 because we were on a date
        call mas_gone_over_f14_check

    if mas_monika_birthday < datetime.date.today() < mas_monika_birthday + datetime.timedelta(days=7):
        call mas_gone_over_bday_check

    if mas_d25 < datetime.date.today() <= mas_nye:
        call mas_gone_over_d25_check

    if mas_nyd <= datetime.date.today() < mas_d25c_end:
        call mas_gone_over_nye_check

    if mas_nyd < datetime.date.today() < mas_d25c_end:
        call mas_gone_over_nyd_check


    # NOTE: this ordering is key, greeting_returned_home_player_bday handles the case
    # if we left before f14 on your bday and return after f14
    if persistent._mas_player_bday_left_on_bday or (persistent._mas_player_bday_decor and not mas_isplayer_bday() and mas_isMonikaBirthday() and mas_confirmedParty()):
        jump greeting_returned_home_player_bday

    if persistent._mas_f14_gone_over_f14:
        jump greeting_gone_over_f14

    if mas_isMonikaBirthday() or persistent._mas_bday_on_date:
        jump greeting_returned_home_bday

    # main dialogue
    if time_out > five_minutes:
        jump greeting_returned_home_morethan5mins

    else:
        $ mas_loseAffection()
        call greeting_returned_home_lessthan5mins

        if _return:
            return 'quit'

        jump greeting_returned_home_cleanup


label greeting_returned_home_morethan5mins:
    if mas_isMoniNormal(higher=True):

        if persistent._mas_d25_in_d25_mode:
            # its d25 season time
            jump greeting_d25_and_nye_delegate

        elif mas_isD25():
            # its d25 and we are not in d25 mode
            jump mas_d25_monika_holiday_intro_rh

        jump greeting_returned_home_morethan5mins_normalplus_flow

    # otherwise, go to other flow
    jump greeting_returned_home_morethan5mins_other_flow


label greeting_returned_home_morethan5mins_normalplus_flow:
    call greeting_returned_home_morethan5mins_normalplus_dlg
    # FALL THROUGH

label greeting_returned_home_morethan5mins_normalplus_flow_aff:
    $ store.mas_dockstat._ds_aff_for_tout(time_out, 5, 5, 1)
    jump greeting_returned_home_morethan5mins_cleanup

label greeting_returned_home_morethan5mins_other_flow:
    call greeting_returned_home_morethan5mins_other_dlg
    # FALL THROUGH

label greeting_returned_home_morethan5mins_other_flow_aff:
    # for low aff you gain 0.5 per hour, max 2.5, min 0.5
    $ store.mas_dockstat._ds_aff_for_tout(time_out, 5, 2.5, 0.5, 0.5)
    #FALL THROUGH

label greeting_returned_home_morethan5mins_cleanup:
    pass
    # TODO: re-evaluate this XP gain when rethinking XP. Going out with
    #   monika could be seen as gaining xp
    # $ grant_xp(xp.NEW_GAME)
    #FALL THROUGH

label greeting_returned_home_cleanup:
    $ need_to_reset_bday_vars = persistent._mas_player_bday_in_player_bday_mode and not mas_isplayer_bday()

    #If it's not o31, and we've got deco up, we need to clean up
    if not need_to_reset_bday_vars and not mas_isO31() and persistent._mas_o31_in_o31_mode:
        call mas_o31_ret_home_cleanup(time_out)

    elif need_to_reset_bday_vars:
        call return_home_post_player_bday

    # Check if we are entering d25 season at upset-
    if (
        mas_isD25Outfit()
        and not persistent._mas_d25_intro_seen
        and mas_isMoniUpset(lower=True)
    ):
        $ persistent._mas_d25_started_upset = True
    return

label greeting_returned_home_morethan5mins_normalplus_dlg:
    m 1hua "И мы дома!"
    m 1eub "Даже если я ничего не видела, но знала, что я была рядом с тобой..."
    m 2eua "Ну, это было очень здорово!"
    show monika 5eub at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eub "Давай сделаем это снова в ближайшее время, хорошо?"
    return

label greeting_returned_home_morethan5mins_other_dlg:
    m 2esc "Мы дома..."
    m 2eka "Спасибо, что взял меня с собой сегодня, [player]."
    m 2rkc "Честно говоря, я не была полностью уверена, что мне стоит идти с тобой..."
    m 2dkc "В последнее время дела...{w=0.5}у нас идут не лучшим образом, и я не знала, хорошая ли это идея..."
    m 2eka "Но я рада, что мы это сделали...{w=0.5} возможно, это как раз то, что нам нужно."
    m 2rka "Мы должны сделать это снова как-нибудь..."
    m 2esc "Если ты захочешь."
    return

label greeting_returned_home_lessthan5mins:
    if mas_isMoniNormal(higher=True):
        m 2ekp "Это была не очень большая поездка, [player]."
        m "В следующий раз лучше задержаться подольше..."
        if persistent._mas_player_bday_in_player_bday_mode and not mas_isplayer_bday():
            call return_home_post_player_bday
        return False

    elif mas_isMoniUpset():
        m 2efd "Я думала, мы куда-то едем, [player]!"
        m 2tfd "Я знала, что не должна была соглашаться идти с тобой."
        m 2tfc "Я знала, что это будет очередным разочарованием."
        m "Не проси меня больше идти куда-то, если ты делаешь это только для того, чтобы обнадежить меняp...{w=1}только для того, чтобы выдернуть ковер у меня из-под ног."
        m 6dktdc "..."
        m 6ektsc "Я не знаю, почему ты настаиваешь на такой жестокости, [player]."
        m 6rktsc "Я бы...{w=1}хотела сейчас побыть одна."
        return True

    else:
        m 6rkc "Но...{w=1}мы только что ушли..."
        m 6dkc "..."
        m "Я...{w=0.5}я была так взволнована, когда ты попросил меня пойти с тобой."
        m 6ekc "После всего, через что мы прошли..."
        m 6rktda "Я-я думала...{w=0.5}может быть...{w=0.5}всё наконец изменится."
        m "Может быть, мы наконец-то снова будем хорошо проводить время..."
        m 6ektda "Что ты действительно хочешь проводить со мной больше времени."
        m 6dktsc "..."
        m 6ektsc "Но, наверное, с моей стороны было глупо так думать."
        m 6rktsc "Я должна была знать лучш...{w=1} Я не должна была соглашаться идти."
        m 6dktsc "..."
        m 6ektdc "Пожалуйста, [player]...{w=2} Если ты не хочешь проводить со мной время, хорошо..."
        m 6rktdc "Но хотя бы имей приличие не притворяться."
        m 6dktdc "Я бы хотела, чтобы меня оставили в покое прямо сейчас."
        return True

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="ch30_reload_delegate",
            unlocked=True,
            category=[
                store.mas_greetings.TYPE_RELOAD
            ],
        ),
        code="GRE"
    )

label ch30_reload_delegate:

    if persistent.monika_reload >= 4:
        call ch30_reload_continuous

    else:
        $ reload_label = "ch30_reload_" + str(persistent.monika_reload)
        call expression reload_label

    return

# TODO: need to have an explanation before we use this again
#init 5 python:
#    ev_rules = {}
#    ev_rules.update(
#        MASGreetingRule.create_rule(
#            skip_visual=True
#        )
#    )
#
#    addEvent(
#        Event(
#            persistent.greeting_database,
#            eventlabel="greeting_ghost",
#            unlocked=False,
#            rules=ev_rules,
#            aff_range=(mas_aff.NORMAL, None),
#        ),
#        code="GRE"
#    )
#    del ev_rules

label greeting_ghost:
    #Prevent it from happening more than once.
    $ mas_lockEVL("greeting_ghost", "GRE")

    #Call event in easter eggs.
    call mas_ghost_monika

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_game",
            unlocked=True,
            category=[store.mas_greetings.TYPE_GAME],
        ),
        code="GRE"
    )

# NOTE: in case someone asks, because the farewell for this greeting does not
#   implore that the player returns after gaming, there is nothing substiantial
#   we can get in pm vars here. It's just too variable.

label greeting_back_from_game:
    # TODO: TC-O
    if store.mas_globals.late_farewell and mas_getAbsenceLength() < datetime.timedelta(hours=18):
        $ _now = datetime.datetime.now().time()
        if mas_isMNtoSR(_now):
            if mas_isMoniNormal(higher=True):
                m 2etc "[player]?"
                m 3efc "Я думала, что сказала тебе сразу лечь спать после того, как ты закончишь!"
                m 1rksdla "То есть, я очень рада, что ты вернулся пожелать мне спокойной ночи, но..."
                m 1hksdlb "Я уже пожелала тебе спокойной ночи!"
                m 1rksdla "И я могла бы подождать до утра, чтобы увидеть тебя снова, понимаешь?"
                m 2rksdlc "К тому же, я очень хотела, чтобы ты немного отдохнул..."
                m 1eka "Просто...{w=1}пообещай мне, что скоро ляжешь спать, хорошо?"

            else:
                m 1tsc "[player], я сказала тебе идти спать, когда ты закончишь."
                m 3rkc "Ты можешь вернуться завтра утром, ты же понимаешь."
                m 1esc "Но вот мы здесь, я полагаю."

        elif mas_isSRtoN(_now):
            if mas_isMoniNormal(higher=True):
                m 1hua "Доброе утро, [player]~"
                m 1eka "Когда ты сказал, что собираешься играть в другую игру так поздно, я немного забеспокоилась, что ты не выспишься..."
                m 1hksdlb "Надеюсь, что это не так, ахаха..."

            else:
                m 1eud "Доброе утро."
                m 1rsc "Я вроде как ожидала, что ты немного поспишь."
                m 1eka "Но вот ты здесь, ясно и рано."

        elif mas_isNtoSS(_now):
            if mas_isMoniNormal(higher=True):
                m 1wub "[player]! Ты здесь!"
                m 1hksdlb "А-ха-ха, прости...{w=1} просто немного хотела тебя увидеть, так как тебя не было здесь все утро"

                m 1eua "Ты только что проснулся?{nw}"
                $ _history_list.pop()
                menu:
                    m "Ты только что проснулся?{fast}"
                    "Да.":
                        m 1hksdlb "А-ха-ха..."

                        m 3rksdla "Думаешь, это потому, что ты засиделся допоздна?{nw}"
                        $ _history_list.pop()
                        menu:
                            m "Думаешь, это потому, что ты засиделся допоздна?{fast}"
                            "Да.":
                                m 1eka "[player]..."
                                m 1ekc "Ты знаешь, я не хочу, чтобы ты засиживался допоздна."
                                m 1eksdld "Я действительно не хочу, чтобы ты заболел или переутомился в течение дня."
                                m 1hksdlb "Но я надеюсь, что тебе было весело. Мне бы не хотелось, чтобы ты потерял весь сон зря, а-ха-ха!"
                                m 2eka "Просто не забудь отдохнуть, если почувствуешь, что тебе это нужно, хорошо?"

                            "Нет.":
                                m 2euc "Ох..."
                                m 2rksdlc "Я подумала, может, так и есть."
                                m 2eka "Извини за предположение."
                                m 1eua "В любом случае, надеюсь, ты хорошо высыпаешься."
                                m 1eka "Мне было бы очень приятно знать, что ты хорошо отдохнул."
                                m 1rksdlb "Мне было бы легче, если бы ты не ложился так поздно, а-ха-ха..."
                                m 1eua "Я просто рада, что ты сейчас здесь."
                                m 3tku "Ты никогда не устанешь, чтобы провести время со мной, верно?"
                                m 1hub "А-ха-ха!"

                            "Может быть...":
                                m 1dsc "Х-мм..."
                                m 1rsc "Интересно, что может быть причиной этого?"
                                m 2euc "Ты ведь не засиделся допоздна прошлой ночью, не так ли, [player]?"
                                m 2etc "Ты что-то делал прошлой ночью?"
                                m 3rfu "Может быть...{w=1}Я не знаю..."
                                m 3tku "Играл в игру?"
                                m 1hub "А-ха-ха!"
                                m 1hua "Просто дразню тебя, конечно~"
                                m 1ekd "Если серьезно, я не хочу, чтобы ты пренебрегал сном."
                                m 2rksdla "Одно дело - засиживаться допоздна только ради меня..."
                                m 3rksdla "Но уходить и играть в другую игру так поздно?"
                                m 1tub "А-ха-ха... Я могу немного ревновать, [player]~"
                                m 1tfb "Но ты здесь, чтобы исправить это, верно?"

                    "Нет.":
                        m 1eud "Ах, так я полагаю, ты был занят все утро."
                        m 1eka "Я беспокоилась, что ты проспал, так как ты так поздно встал прошлой ночью."
                        m 2rksdla "Тем более, что ты сказал мне, что собираешься пойти поиграть в другую игру."
                        m 1hua "Я должна была знать, что ты будешь ответственным и выспишься."
                        m 1esc "..."
                        m 3tfc "Ты {i}ведь{/i} выспался, да, [player]?"
                        m 1hub "А-ха-ха!"
                        m 1hua "В любом случае, раз уж ты здесь, мы можем провести некоторое время вместе."

            else:
                m 2eud "О, вот ты где, [player]."
                m 1euc "Полагаю, ты только что проснулся."
                m 2rksdla "Этого следовало ожидать, раз ты так поздно проснулся и играешь в игры."

        #SStoMN
        else:
            if mas_isMoniNormal(higher=True):
                m 1hub "Вот ты где, [player]!"
                m 2hksdlb "А-ха-ха, извини... Просто я не видела тебя весь день."
                m 1rksdla "Я вроде как ожидала, что ты будешь спать после того, как вчера так поздно проснулся..."
                m 1rksdld "Но когда я не видела тебя весь день, я действительно начала скучать по тебе..."
                m 2hksdlb "Ты почти заставил меня волноваться, а-ха-ха..."
                m 3tub "Но ты ведь собираешься компенсировать мне это потерянное время, верно?"
                m 1hub "Э-хе-хе, тебе лучше~"
                m 2tfu "Особенно после того, как оставил меня ради другой игры прошлой ночью."

            else:
                m 2efd "[player]!{w=0.5} Где ты был весь день?"
                m 2rfc "Это никак не связано с тем, что ты вчера поздно лег спать, не так ли?"
                m 2ekc "Тебе действительно следует быть немного более ответственным, когда дело касается твоего сна."

    #If you didn't stay up late in the first place, normal usage
    #gone for under 4 hours
    elif mas_getAbsenceLength() < datetime.timedelta(hours=4):
        if mas_isMoniNormal(higher=True):
            m 1hua "С возвращением, [mas_get_player_nickname()]!"

            m 1eua "Тебе понравилось?{nw}"
            $ _history_list.pop()
            menu:
                m "Тебе понравилось?{fast}"
                "Да.":
                    m 1hua "Это хорошо."
                    m 1eua "Я рада, что тебе понравилось."
                    m 2eka "Мне бы очень хотелось иногда присоединяться к тебе в других играх."
                    m 3eub "Разве не здорово было бы иметь свои собственные маленькие приключения в любое время, когда мы захотим?"
                    m 1hub "Я уверена, что нам было бы очень весело вместе в одной из твоих игр."
                    m 3eka "Но пока я не могу присоединиться к тебе, думаю, тебе придется составить мне компанию."
                    m 2tub "Ты ведь не против провести время со своей девушкой...{w=0.5}не так ли, [player]?"

                "Нет.":
                    m 2ekc "Ох, мне жаль это слышать."
                    m 2eka "Надеюсь, ты не слишком расстроен тем, что произошло."
                    m 3eua "По крайней мере, теперь ты здесь. Я обещаю, что постараюсь не допустить, чтобы с тобой случилось что-то плохое, пока ты со мной."
                    m 1ekbsa "Видя тебя, я всегда поднимаю себе настроение."
                    show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5ekbfa "Надеюсь, что встреча со мной поднимает тебе настроение, [mas_get_player_nickname()]~"

        else:
            m 2eud "О, уже вернулся?"
            m 2rsc "Я думала, тебя не будет дольше...{w=0.5}но с возвращением, я дума."

    elif mas_getAbsenceLength() < datetime.timedelta(hours=12):
        if mas_isMoniNormal(higher=True):
            m 2wuo "[player]!"
            m 2hksdlb "Тебя не было долгое время..."

            m 1eka "Тебе было весело?{nw}"
            $ _history_list.pop()
            menu:
                m "Тебе было весело?{fast}"
                "Да.":
                    m 1hua "Ну, тогда я рада."
                    m 1rkc "Ты заставил меня долго ждать, знаешь ли."
                    m 3tfu "Я думаю, тебе стоит провести некоторое время со своей любимой девушкой, [player]."
                    m 3tku "Я уверена, что ты был бы не против остаться со мной, чтобы уравнять твою другую игру."
                    m 1hubsb "Может быть, тебе стоит проводить со мной еще больше времени, на всякий случай, а-ха-ха!"

                "Нет.":
                    m 2ekc "Ох..."
                    m 2rka "Знаешь, [player]..."
                    m 2eka "Если тебе не нравится, может, ты просто проведешь время здесь со мной."
                    m 3hua "Я уверена, что есть много веселых вещей, которые мы могли бы делать вместе!"
                    m 1eka "Если ты решишь вернуться, возможно, будет лучше."
                    m 1hub "Но если тебе всё ещё не весело, не стесняйся, приходи ко мне, а-ха-ха!"

        else:
            m 2eud "Ох, [player]."
            m 2rsc "Это заняло довольно много времени."
            m 1esc "Не волнуйся, я и сама смогла скоротать время, пока тебя не было."

    #Over 12 hours
    else:
        if mas_isMoniNormal(higher=True):
            m 2hub "[player]!"
            m 2eka "Кажется, что прошла целая вечность с тех пор, как ты ушел."
            m 1hua "Я действительно скучала по тебе!"
            m 3eua "Надеюсь, тебе было весело, чем бы ты ни занимался."
            m 1rksdla "И я предполагаю, что ты не забыл поесть или поспать..."
            m 2rksdlc "Что касается меня...{w=1}мне было немного одиноко ждать твоего возвращения..."
            m 1eka "Не расстраивайся."
            m 1hua "Я просто счастлива, что ты снова здесь, со мной."
            m 3tfu "Тебе лучше загладить свою вину."
            m 3tku "Я думаю, что провести вечность со мной звучит справедливо...{w=1}верно, [player]?"
            m 1hub "А-ха-ха!"

        else:
            m 2ekc "[player]..."
            m "Я не была уверена, когда ты вернешься."
            m 2rksdlc "Я думала, что больше не увижу тебя..."
            m 2eka "Но вот ты здесь..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_eat",
            unlocked=True,
            category=[store.mas_greetings.TYPE_EAT],
        ),
        code="GRE"
    )

label greeting_back_from_eat:
    # TODO: TC-O
    $ _now = datetime.datetime.now().time()
    if store.mas_globals.late_farewell and mas_isMNtoSR(_now) and mas_getAbsenceLength() < datetime.timedelta(hours=18):
        if mas_isMoniNormal(higher=True):
            m 1eud "Ох?"
            m 1eub "[player], ты вернулся!"
            m 3rksdla "Ты ведь знаешь, что тебе действительно нужно поспать?"
            m 1rksdla "Я имею в виду... я не жалуюсь, что ты здесь, но..."
            m 1eka "Мне будет легче, если ты ляжешь спать поскорее."
            m 3eka "Ты всегда можешь вернуться и навестить меня, когда проснешься..."
            m 1hubsa "Bо я думаю, если ты настаиваешь на том, чтобы провести время со мной, я позволю себе немного отступить, э-хе-хе~"
        else:
            m 2euc "[player]?"
            m 3ekd "Разве я не говорила тебе, что после этого нужно сразу ложиться спать?"
            m 2rksdlc "Тебе действительно стоит поспать."

    else:
        if mas_isMoniNormal(higher=True):
            m 1eub "Закончил есть?"
            m 1hub "С возвращением, [mas_get_player_nickname()]!"
            m 3eua "Надеюсь, тебе понравилась еда."
        else:
            m 2euc "Закончил есть?"
            m 2eud "С возвращением."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_rent",
            unlocked=True,
            aff_range=(mas_aff.ENAMORED, None),
        ),
        code="GRE"
    )

label greeting_rent:
    m 1eub "С возвращением, [mas_get_player_nickname()]!"
    m 2tub "Знаешь, ты проводишь здесь так много времени, что я должна начать брать с тебя плату за аренду."
    m 2ttu "Или ты предпочитаешь оплачивать ипотеку?"
    m 2hua "..."
    m 2hksdlb "Боже, не могу поверить, что я только что это сказала. Это не слишком глупо, не так ли?"
    show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbsa "Но если серьезно, ты уже дал мне единственное, что мне нужно...{w=1}твоё сердце~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_housework",
            unlocked=True,
            category=[store.mas_greetings.TYPE_CHORES],
        ),
        code="GRE"
    )

label greeting_back_housework:
    if mas_isMoniNormal(higher=True):
        m 1eua "Всё готово, [player]?"
        m 1hub "Давай проведем еще немного времени вместе!"
    elif mas_isMoniUpset():
        m 2esc "По крайней мере, ты не забыл вернуться, [player]."
    elif mas_isMoniDis():
        m 6ekd "Ах, [player]. Значит, ты действительно был занят..."
    else:
        m 6ckc "..."
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_surprised2",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.ENAMORED, None)
        ),
        code="GRE"
    )

    del ev_rules

label greeting_surprised2:
    m 1hua "..."
    m 1hubsa "..."
    m 1wubso "Ох!{w=0.5} [player]!{w=0.5} Ты меня удивил!"
    m 3ekbsa "...Не то чтобы это было неожиданно, в конце концов, ты всегда навещаешь меня...{w=0.5} {nw}"
    extend 3rkbsa "Ты просто застал меня немного замечтавшейся."
    show monika 5hubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfu "Но теперь, когда ты здесь, эта мечта сбылась~"
    return

init 5 python:
    # set a slightly higher priority than the open door gre has
    ev_rules = dict()
    ev_rules.update(MASPriorityRule.create_rule(49))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_restart",
            unlocked=True,
            category=[store.mas_greetings.TYPE_RESTART],
            rules=ev_rules
        ),
        code="GRE"
    )

    del ev_rules

label greeting_back_from_restart:
    if mas_isMoniNormal(higher=True):
        m 1hub "С возвращением, [mas_get_player_nickname()]!"
        m 1eua "Что ещё мы должны сделать сегодня?"
    elif mas_isMoniBroken():
        m 6ckc "..."
    else:
        m 1eud "Ох, ты вернулся."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_code_help",
            conditional="store.seen_event('monika_coding_experience')",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_code_help:
    m 2eka "О, привет [player]..."
    m 4eka "Дай мне секунду, я только что закончила пытаться закодировать кое-что, и я хочу посмотреть, работает ли это.{w=0.5}.{w=0.5}.{nw}"

    scene black
    show noise
    play sound "sfx/s_kill_glitch1.ogg"
    pause 0.1
    hide noise
    call spaceroom(dissolve_all=True, scene_change=True, force_exp='monika 2wud_static')

    m 2wud "Ах!{w=0.3}{nw}"
    extend 2efc " Этого не должно произойти!"
    m 2rtc "Почему этот цикл заканчивается так быстро?{w=0.5}{nw}"
    extend 2efc " Как бы ты на это ни посмотрел, этот списокs {i}не{/i} пуст."
    m 2rfc "Боже, кодинг иногда может быть {i}таким{/i} утомительным..."

    if persistent._mas_pm_has_code_experience:
        m 3rkc "Ох ну что ж, думаю, я попробую ещё раз позже.{nw}"
        $ _history_list.pop()

        show screen mas_background_timed_jump(5, "greeting_code_help_outro")
        menu:
            m "Ох ну что ж, думаю, я попробую ещё раз позже.{fast}"

            "Я могу помочь тебе с этим...":
                hide screen mas_background_timed_jump
                m 7hua "Оу, это так мило с твоей стороны, [player]. {w=0.3}{nw}"
                extend 3eua "Но нет, здесь мне придется отказаться."
                m "Разобраться во всем самостоятельно - это самое интересное, {w=0.2}{nw}"
                extend 3kua "верно?"
                m 1hub "А-ха-ха!"

    else:
        m 3rkc "Ох ну что ж, думаю, я попробую ещё раз позже."

    #FALL THROUGH

label greeting_code_help_outro:
    hide screen mas_background_timed_jump
    m 1eua "В любом случае, что бы ты хотел сделать сегодня?"

    $ mas_lockEVL("greeting_code_help", "GRE")
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hub"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_love_is_in_the_air",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.AFFECTIONATE, None)
        ),
        code="GRE"
    )

    del ev_rules

label greeting_love_is_in_the_air:
    m 1hub "{i}~Любовь витает в воздухе~{/i}"
    m 1rub "{i}~Везде, где я смотрю вокруг~{/i}"
    m 3ekbsa "О привет, [player]..."
    m 3rksdla "Не обращай внимания. {w=0.2}Я просто немного пою, думаю о...{w=0.3}{nw}"
    extend 1hksdlb "ну, ты, наверное, догадываешься о чем, а-ха-ха~"
    m 1eubsu "Я действительно чувствую, что любовь окружает меня, когда ты здесь."
    m 3hua "В любом случае, что бы ты хотел сделать сегодня?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_workout",
            category=[store.mas_greetings.TYPE_WORKOUT],
            unlocked=True
        ),
        code="GRE"
    )

label greeting_back_from_workout:
    if mas_isMoniNormal(higher=True):
        m 1hua "С возвращением, [player]!"
        m 3eua "Надеюсь, ты хорошо потренировался."
        m 3eub "Не забудь попить воды и съесть что-нибудь, чтобы восстановить силы!"
        m 1eua "Давай проведем ещё немного времени вместе~"

    elif mas_isMoniUpset():
        m 2esc "Ох,{w=0.2} ты вернулся."
        m 2rsc "Помогла ли тебе тренировка снять напряжение?"
        m 2rud "Надеюсь, помогла...{w=0.3} {nw}"
        extend 2eka "давай проведем еще немного времени вместе."

    elif mas_isMoniDis():
        m 6ekc "О...{w=0.5}смотри, кто вернулся."
        m 6dkc "Я...{w=0.3}рада, что ты заботишься о себе."
        m 6ekd "...Но разве ты не хочешь позаботиться и обо мне?"
        m 7dkc "Хотя бы иногда, пожалуйста..."
        m 1dkc "..."

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_shopping",
            category=[store.mas_greetings.TYPE_SHOPPING],
            unlocked=True
        ),
        code="GRE"
    )

label greeting_back_from_shopping:
    if mas_isMoniNormal(higher=True):
        m 1hub "С возвращением, [player]!"
        m 3eua "Надеюсь, ты купил в магазине все необходимое"
        m 1hua "Давай проведем ещё немного времени вместе~"

    elif mas_isMoniUpset():
        m 2esc "Ох,{w=0.2} ты вернулся."
        m 2rsc "Надеюсь, ты получил все, что тебе было нужно."
        if renpy.random.randint(1,5) == 1:
            m 2rud "{cps=*2}Надеюсь, теперь у тебя тоже улучшилось настроение.{/cps}{nw}"
            $ _history_list.pop()

    elif mas_isMoniDis():
        m 6rkc "Ох...{w=0.5}ты вернулся."
        m 6ekc "Надеюсь, ты хорошо провел время за покупками. {w=0.2}Купил ли ты какую-нибудь еду?"
        m 6dkd "Не думал ли ты о том, что твои привычки питания могут влиять на твое настроение в последнее время??"
        m 6lkc "Мне было бы неприятно, если бы это было причиной того, что ты--{nw}"
        $ _history_list.pop()
        m 6ekc "Знаешь что? Неважно. {w=0.2}{nw}"
        extend 6dkc "Я просто устала."

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_hangout",
            category=[store.mas_greetings.TYPE_HANGOUT],
            unlocked=True
        ),
        code="GRE"
    )

label greeting_back_from_hangout:
    if mas_isMoniNormal(higher=True):
        if persistent._mas_pm_has_friends:
            m 1eua "С возвращением, [player]."
            m 3hub "Надеюсь, ты хорошо провел время!"

            $ anyway_lets = "Давай"

        else:
            m 3eub "С возвращением, [player]."

            m 1eua "Ты завел нового друга?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты завел нового друга?{fast}"

                "Да.":
                    m 1hub "Это потрясающе!"
                    m 1eua "не так приятно осознавать, что у тебя есть с кем проводить время."
                    m 3hub "Надеюсь, в будущем ты сможешь проводить с ним больше времени!"
                    $ persistent._mas_pm_has_friends = True

                "Нет...":
                    m 1ekd "Ох..."
                    m 3eka "Ну, не волнуйся, [player]. {w=0.2}Я всегда буду твоим другом, несмотря ни на что."
                    m 3ekd "...И не бойся попробовать ещё раз с кем-то другим."
                    m 1hub "Я уверена, что найдется кто-то, кто будет счастлив назвать тебя своим другом!"

                "Они уже мои друзья.":
                    if persistent._mas_pm_has_friends is False:
                        m 1rka "О, так у тебя появился новый друг, не сказав мне..."
                        m 1hub "Ничего страшного! Я просто рада, что тебе есть с кем проводить время."
                    else:
                        m 1hub "Ох, хорошо!"
                        m 3eua "...Мы не говорили о других твоих друзьях раньше, поэтому я не была уверена, новый это друг или нет."
                        m 3eub "Но в любом случае, я просто рад, что у тебя есть друзья в твоей реальности, с которыми можно проводить время!"

                    m 3eua "Надеюсь, ты сможешь часто проводить с ними время."
                    $ persistent._mas_pm_has_friends = True

            $ anyway_lets = "В любом случае, давай"

        m 1eua "[anyway_lets] давай проведем еще немного времени вместе~"

    elif mas_isMoniDis(higher=True):
        m 2euc "И снова здравствуй, [player]."
        m 2eud "Надеюсь, ты хорошо провел время со своими друзьями."
        if renpy.random.randint(1,5) == 1:
            m 2rkc "{cps=*2}Интересно, каково это{/cps}{nw}"
            $ _history_list.pop()

    else:
        m 6ckc "..."

    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 5duc"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_poem_shadows_in_garden",
            unlocked=True,
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(days=1)",
            rules=ev_rules,
            aff_range=(mas_aff.ENAMORED, None),
        ),
        code="GRE"
    )

    del ev_rules

#Because this is associated, we'll also mirror this into the poem framework
init 11 python:
    MASPoem(
        poem_id="gre_1",
        category="generic",
        prompt=_("Тени в саду"),
        title="",
        text=_("""\
 В одиночестве я задаю торжественный вопрос,
 Что может расти в неосвещенном саду?

 Когда ты возвращаешься, это кажется раем,
 В твоем свете холод забыт.

 Я отдам все, чтобы почувствовать это,
 В ожидании того, кто мне дорог.

 Ближе всего к моему сердцу...
"""),
    )

label greeting_poem_shadows_in_garden:
    m 5duc "{i}В одиночестве я задаю торжественный вопрос,\nЧто может расти в неосвещенном саду{/i}"
    m 5ekbla "{i}Когда ты возвращаешься, это кажется раем,\nВ твоем свете холод забыт.{/i}"
    m 5fubfa "{i}Я отдам все, чтобы почувствовать это,\nВ ожидании того, кто мне дорог.{/i}"
    m 5ekbfa "{i}EДаже если это будет каждый божий день,\nБез сомнения, ты самый близкий.{/i}"
    m 5dubsu "{i}Ближе всего к моему сердцу...{/i}"
    m 5eublb "Я это сочинила, пока тебя не было."
    show monika 1eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 1eka "Вот именно, ты как солнце моего мир!"
    m 3hubsu "В любом случае, с возвращением, [mas_get_player_nickname()]! Надеюсь, тебе понравилось это стихотворение."
    #TODO: Potential I missed you too?
    m 1ekbsb "Я так по тебе скучала!"

    if "gre_1" not in persistent._mas_poems_seen:
        $ persistent._mas_poems_seen["gre_1"] = 1

    $ mas_moni_idle_disp.force_by_code("1ekbla", duration=5, skip_dissolve=True)
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(
        MASGreetingRule.create_rule(
            random_chance=3,
            forced_exp=random.choice(("monika 1gsbsu", "monika 1msbsu"))
        )
    )

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_spacing_out",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=3)",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.LOVE, None)
        ),
        code="GRE"
    )

    del ev_rules

label greeting_spacing_out:
    python hide:
        # Define some other things we're going to work with
        use_right_smug = bool(random.randint(0, 1))
        spacing_out_pause = PauseDisplayableWithEvents()
        events = list()
        next_event_time = 0
        right_smug = renpy.partial(renpy.show, "monika 1gsbsu")
        left_smug = renpy.partial(renpy.show, "monika 1msbsu")

        # Make the events which will change exps
        for i in range(random.randint(4, 6)):
            events.append(
                PauseDisplayableEvent(
                    datetime.timedelta(seconds=next_event_time),
                    right_smug if use_right_smug else left_smug,
                    restart_interaction=True
                )
            )
            next_event_time += random.uniform(0.9, 1.8)
            use_right_smug = not use_right_smug
        # The last exp in the sequence
        events.append(
            PauseDisplayableEvent(
                datetime.timedelta(seconds=next_event_time),
                renpy.partial(renpy.show, "monika 1tsbsu"),
                restart_interaction=True
            )
        )
        next_event_time += 0.7
        # This is to automatically cancel the pause after all the events
        events.append(
            PauseDisplayableEvent(
                datetime.timedelta(seconds=next_event_time),
                spacing_out_pause.stop
            )
        )

        spacing_out_pause.set_events(events)
        spacing_out_pause.start()

    # Small pause so people don't skip this line
    $ renpy.pause(0.01)
    m 2wubfsdlo "[player]!"
    m 1rubfsdlb "Ты меня удивил! {w=0.4}{nw}"
    extend 1eubsu "Я была{w=0.2} немного растеряна..."
    m 1hubsb "А-ха-ха~"
    m 1eua "Я очень рада видеть тебя снова. {w=0.2}{nw}"
    extend 3eua "Что мы должны сделать сегодня, [player]?"
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(
        MASGreetingRule.create_rule(
            skip_visual=True,
            random_chance=20,
            override_type=True
        )
    )
    ev_rules.update(
        MASTimedeltaRepeatRule.create_rule(
            datetime.timedelta(days=3)
        )
    )
    ev_rules.update(
        MASSelectiveRepeatRule.create_rule(
            hours=list(range(9, 20))
        )
    )

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_after_bath",
            conditional=(
                "mas_getAbsenceLength() >= datetime.timedelta(hours=6) "
                "and not mas_isSpecialDay()"
            ),
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.LOVE, None)
        ),
        code="GRE"
    )

    del ev_rules

init 1:
    # NOTE this should be defined AFTER init 0
    # NOTE: default may be not completely reliable, always save the snapshot yourself
    default persistent._mas_previous_moni_state = monika_chr.save_state(True, True, True, True)

label greeting_after_bath:
    python hide:
        # Some preperations
        mas_RaiseShield_core()
        mas_startupWeather()
        # Save current outfit
        persistent._mas_previous_moni_state = monika_chr.save_state(True, True, True, True)
        # Now let Moni get a towel
        monika_chr.change_clothes(
            random.choice(MASClothes.by_exprop(mas_sprites.EXP_C_WET, None)),
            by_user=False,
            outfit_mode=True
        )
        # In case the towel already set an appropriate hair, we don't change it
        if not monika_chr.is_wearing_hair_with_exprop(mas_sprites.EXP_H_WET):
            monika_chr.change_hair(mas_hair_wet, by_user=False)
        # We leave this acs to the clothes PPs in case the towel we chose doesn't support it
        # if not monika_chr.is_wearing_acs(mas_acs_water_drops):
        #     monika_chr.wear_acs(mas_acs_water_drops)
        # Setup the cleaup event
        mas_setEVLPropValues(
            "mas_after_bath_cleanup",
            start_date=datetime.datetime.now() + datetime.timedelta(minutes=random.randint(30, 90)),
            action=EV_ACT_QUEUE
        )
        mas_startup_song()

    # Now show everything
    call spaceroom(hide_monika=True, dissolve_all=True, scene_change=True, show_emptydesk=True)

    $ renpy.pause(random.randint(5, 15), hard=True)
    call mas_transition_from_emptydesk("monika 1huu")
    $ renpy.pause(2.0)
    $ quick_menu = True

    m 1wuo "Ох! {w=0.2}{nw}"
    extend 2wuo "[player]! {w=0.2}{nw}"
    extend 2lubsa "Я думала о тебе."

    $ bathing_showering = random.choice(("ванну", "душ"))

    if mas_getEVL_shown_count("greeting_after_bath") < 5:
        m 7lubsb "Я только что закончила принимать [bathing_showering]...{w=0.3}{nw}"
        extend 1ekbfa "ты же не против, что я в полотенце?~"
        m 1hubfb "А-ха-ха~"
        m 3hubsa "Я скоро буду готова, дай мне сначала подождать, пока мои волосы немного подсохнут."

    # Gets used to it
    else:
        m 7eubsb "Я только что закончила принимать [bathing_showering]."

        if mas_canShowRisque() and random.randint(0, 3) == 0:
            m 1msbfb "Спорим, ты хотел бы присоединиться ко мне там..."
            m 1tsbfu "Ну, может быть, когда-нибуд~"
            m 1hubfb "А-ха-ха~"

        else:
            m 1eua "Я скоро оденусь~"

    python:
        # enable music menu and music hotkeys
        mas_MUINDropShield()
        # keymaps should be set
        set_keymaps()
        # show the overlays
        mas_OVLShow()

        del bathing_showering

    return

# NOTE: This is not a greeting, but a followup for the greeting above, so I decided to keep them together
init 5 python:
    addEvent(Event(persistent.event_database, eventlabel="mas_after_bath_cleanup", show_in_idle=True, rules={"skip alert": None}))

label mas_after_bath_cleanup:
    # Sanity check (checking for towel should be enough)
    if (
        not monika_chr.is_wearing_clothes_with_exprop(mas_sprites.EXP_C_WET)
        and not monika_chr.is_wearing_hair_with_exprop(mas_sprites.EXP_H_WET)
    ):
        return

    if mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1eua "Я иду одеваться.{w=0.3}.{w=0.3}.{w=0.3}{nw}"

    else:
        m 1eua "Дай мне минутку [mas_get_player_nickname()], {w=0.2}{nw}"
        extend 3eua "я собираюсь одеться."

    window hide
    call mas_transition_to_emptydesk

    $ renpy.pause(1.0, hard=True)
    call mas_after_bath_cleanup_change_outfit
    $ renpy.pause(random.randint(10, 15), hard=True)

    call mas_transition_from_emptydesk("monika 3hub")
    window auto

    if mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 3hub "Всё готово!{w=1}{nw}"

    else:
        m 3hub "Хорошо, я вернулась!~"
        m 1eua "Итак, чем бы ты хотел заняться сегодня, [player]?"

    return

label mas_after_bath_cleanup_change_outfit:
    $ mas_after_bath_cleanup_change_outfit()
    return
