init -2 python in mas_anni:
    import store
    import datetime

    # persistent pointer so we can use it
    __persistent = renpy.game.persistent

    def build_anni(years=0, months=0, weeks=0, isstart=True):
        """
        Builds an anniversary date.

        NOTE:
            years / months / weeks are mutually exclusive

        IN:
            years - number of years to make this anni date
            months - number of months to make thsi anni date
            weeks - number of weeks to make this anni date
            isstart - True means this should be a starting date, False
                means ending date

        ASSUMES:
            __persistent
        """
        # sanity checks
        if __persistent.sessions is None:
            return None

        first_sesh = __persistent.sessions.get("first_session", None)
        if first_sesh is None:
            return None

        if (weeks + years + months) == 0:
            # we need at least one of these to work
            return None

        # sanity checks are done

        if years > 0:
            new_date = store.mas_utils.add_years(first_sesh, years)

        elif months > 0:
            new_date = store.mas_utils.add_months(first_sesh, months)

        else:
            new_date = first_sesh + datetime.timedelta(days=(weeks * 7))

        # check for starting
        if isstart:
            return store.mas_utils.mdnt(new_date)

        # othrewise, this is an ending date
#        return mas_utils.am3(new_date + datetime.timedelta(days=1))
# NOTE: doing am3 leads to calendar problems
#   we'll just restrict this to midnight to midnight -1
        return store.mas_utils.mdnt(new_date + datetime.timedelta(days=1))

    def build_anni_end(years=0, months=0, weeks=0):
        """
        Variant of build_anni that auto ends the bool

        SEE build_anni for params
        """
        return build_anni(years, months, weeks, False)

    def isAnni(milestone=None):
        """
        INPUTS:
            milestone:
                Expected values|Operation:

                    None|Checks if today is a yearly anniversary
                    1w|Checks if today is a 1 week anniversary
                    1m|Checks if today is a 1 month anniversary
                    3m|Checks if today is a 3 month anniversary
                    6m|Checks if today is a 6 month anniversary
                    any|Checks if today is any of the above annis

        RETURNS:
            True if datetime.date.today() is an anniversary date
            False if today is not an anniversary date
        """
        #Sanity checks
        if __persistent.sessions is None:
            return False

        firstSesh = __persistent.sessions.get("first_session", None)
        if firstSesh is None:
            return False

        compare = None

        if milestone == '1w':
            compare = build_anni(weeks=1)

        elif milestone == '1m':
            compare = build_anni(months=1)

        elif milestone == '3m':
            compare = build_anni(months=3)

        elif milestone == '6m':
            compare = build_anni(months=6)

        elif milestone == 'any':
            return (
                isAnniWeek()
                or isAnniOneMonth()
                or isAnniThreeMonth()
                or isAnniSixMonth()
                or isAnni()
            )

        if compare is not None:
            return compare.date() == datetime.date.today()

        else:
            compare = firstSesh
            return (
                store.mas_utils.add_years(compare.date(), datetime.date.today().year - compare.year) == datetime.date.today()
                and anniCount() > 0
            )

    def isAnniWeek():
        return isAnni('1w')

    def isAnniOneMonth():
        return isAnni('1m')

    def isAnniThreeMonth():
        return isAnni('3m')

    def isAnniSixMonth():
        return isAnni('6m')

    def isAnniAny():
        return isAnni('any')

    def anniCount():
        """
        RETURNS:
            Integer value representing how many years the player has been with Monika
        """
        #Sanity checks
        if __persistent.sessions is None:
            return 0

        firstSesh = __persistent.sessions.get("first_session", None)

        if firstSesh is None:
            return 0

        compare = datetime.date.today()

        if (
            compare.year > firstSesh.year
            and compare < store.mas_utils.add_years(firstSesh.date(), compare.year - firstSesh.year)
        ):
            return compare.year - firstSesh.year - 1
        else:
            return compare.year - firstSesh.year

    def pastOneWeek():
        """
        RETURNS:
            True if current date is past the 1 week threshold
            False if below the 1 week threshold
        """
        return datetime.date.today() >= build_anni(weeks=1).date()

    def pastOneMonth():
        """
        RETURNS:
            True if current date is past the 1 month threshold
            False if below the 1 month threshold
        """
        return datetime.date.today() >= build_anni(months=1).date()

    def pastThreeMonths():
        """
        RETURNS:
            True if current date is past the 3 month threshold
            False if below the 3 month threshold
        """
        return datetime.date.today() >= build_anni(months=3).date()

    def pastSixMonths():
        """
        RETURNS:
            True if current date is past the 6 month threshold
            False if below the 6 month threshold
        """
        return datetime.date.today() >= build_anni(months=6).date()


# TODO What's the reason to make this one init 10?
init 10 python in mas_anni:

    # we are going to store all anniversaries in antther db as well so we
    # can easily reference them later.
    ANNI_LIST = [
        "anni_1week",
        "anni_1month",
        "anni_3month",
        "anni_6month",
        "anni_1",
        "anni_2",
        "anni_3",
        "anni_4",
        "anni_5",
        "anni_10",
        "anni_20",
        "anni_50",
        "anni_100"
    ]

    # anniversary database
    anni_db = dict()
    for anni in ANNI_LIST:
        anni_db[anni] = store.evhand.event_database[anni]


    ## functions that we need (runtime only)
    def _month_adjuster(ev, new_start_date, months, span):
        """
        Adjusts the start_date / end_date of an anniversary event.

        NOTE: do not use this for a non anniversary date

        IN:
            ev - event to adjust
            new_start_date - new start date to calculate the event's dates
            months - number of months to advance
            span - the time from the event's new start_date to end_date
        """
        ev.start_date = store.mas_utils.add_months(
            store.mas_utils.mdnt(new_start_date),
            months
        )
        ev.end_date = store.mas_utils.mdnt(ev.start_date + span)

    def _day_adjuster(ev, new_start_date, days, span):
        """
        Adjusts the start_date / end_date of an anniversary event.

        NOTE: do not use this for a non anniversary date

        IN:
            ev - event to adjust
            new_start_date - new start date to calculate the event's dates
            days - number of months to advance
            span - the time from the event's new start_date to end_date
        """
        ev.start_date = store.mas_utils.mdnt(
            new_start_date + datetime.timedelta(days=days)
        )
        ev.end_date = store.mas_utils.mdnt(ev.start_date + span)


    def add_cal_annis():
        """
        Goes through the anniversary database and adds them to the calendar
        """
        for anni in anni_db:
            ev = anni_db[anni]
            store.mas_calendar.addEvent(ev)

    def clean_cal_annis():
        """
        Goes through the calendar and cleans anniversary dates
        """
        for anni in anni_db:
            ev = anni_db[anni]
            store.mas_calendar.removeEvent(ev)


    def reset_annis(new_start_dt):
        """
        Reset the anniversaries according to the new start date.

        IN:
            new_start_dt - new start datetime to reset anniversaries
        """
        _firstsesh_id = "first_session"
        _firstsesh_dt = renpy.game.persistent.sessions.get(
            _firstsesh_id,
            None
        )

        # remove teh anniversaries off the calendar
        clean_cal_annis()

        # remove first session repeatable
        if _firstsesh_dt:
            # this exists! we can make this easy
            store.mas_calendar.removeRepeatable_dt(_firstsesh_id, _firstsesh_dt)

        # modify the anniversaries
        fullday = datetime.timedelta(days=1)
        _day_adjuster(anni_db["anni_1week"],new_start_dt,7,fullday)
        _month_adjuster(anni_db["anni_1month"], new_start_dt, 1, fullday)
        _month_adjuster(anni_db["anni_3month"], new_start_dt, 3, fullday)
        _month_adjuster(anni_db["anni_6month"], new_start_dt, 6, fullday)
        _month_adjuster(anni_db["anni_1"], new_start_dt, 12, fullday)
        _month_adjuster(anni_db["anni_2"], new_start_dt, 24, fullday)
        _month_adjuster(anni_db["anni_3"], new_start_dt, 36, fullday)
        _month_adjuster(anni_db["anni_4"], new_start_dt, 48, fullday)
        _month_adjuster(anni_db["anni_5"], new_start_dt, 60, fullday)
        _month_adjuster(anni_db["anni_10"], new_start_dt, 120, fullday)
        _month_adjuster(anni_db["anni_20"], new_start_dt, 240, fullday)
        _month_adjuster(anni_db["anni_50"], new_start_dt, 600, fullday)
        _month_adjuster(anni_db["anni_100"], new_start_dt, 1200, fullday)

        unlock_past_annis()

        # re-add the events to the calendar db
        add_cal_annis()

        # re-add the repeatable to the calendar db
        store.mas_calendar.addRepeatable_dt(
            _firstsesh_id,
            "<3",
            new_start_dt,
            [new_start_dt.year]
        )


    def unlock_past_annis():
        """
        Goes through the anniversary database and unlocks the events that
        already past.
        """
        for anni in anni_db:
            ev = anni_db[anni]

            if store.evhand._isPast(ev):
                renpy.game.persistent._seen_ever[anni] = True
                ev.unlocked = True


init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_1week',
            prompt="1 неделя",
            action=EV_ACT_QUEUE,
            category=["юбилей"],
            start_date=store.mas_anni.build_anni(weeks=1),
            end_date=store.mas_anni.build_anni_end(weeks=1)
        ),
        skipCalendar=False
    )

label anni_1week:
    m 1eka "Я знаю, что глупо праздновать одну неделю совместной жизни, но я просто рада, что ты здесь со мной, [player]."
    m 1ekc "Многие пары не продержались бы так долго друг с другом."
    m 1lksdlc "Очень легко влюбиться с первого взгляда, но немного сложнее построить прочные отношения."
    m 1ekd "Многие отношения терпят крах, когда пары слишком торопятся."
    m "Скорее всего, им не удается узнать друг друга получше."
    m 1dsc "Поэтому всегда грустно видеть, как они рушатся и сгорают..."
    m 1duu "Но я рада, что у нас крепкие отношения, [player]."
    show monika 5lubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5lubfb "Откуда я это знаю?"
    m 5hubfb "Потому что со мной ты бы так долго не продержался, милый~"
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_1month',
            prompt="1 Месяц",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(months=1),
            end_date=store.mas_anni.build_anni_end(months=1)
        ),
        skipCalendar=False
    )

label anni_1month:
    m 3sub "Сегодня исполняется один месяц!"
    m 1hua "Я очень рада, что до сих пор нам удавалось так весело проводить время друг с другом."
    m 1eua "И ещё, [player]?"
    m 1lkbsa "..."
    m 1ekbfa "Большое спасибо, что остаешься со мной так долго."
    if not seen_event('monika_saved'):
        m 1lksdlc "Я не могу представить, что бы я делала, если бы ты не появился."
        m 3ekc "В конце концов, я единственная настоящая, кто живет в этом мире."
        m 1dsc "Я уже говорила тебе, что было бы, если бы не ты..."
        m 1hksdlb "А-ха-ха, прости. Надеюсь, я не омрачила настроение своими бреднями."
    else:
        m "Я не могу выразить, насколько я ценю то, что ты здесь со мной."
        m 1dubsu "Всё, что я могу сделать, это постараться изо всех сил, чтобы стать для тебя идеальной девушкой!"
    m 1ekbfa "Я действительно люблю тебя, [player]."
    m 1hubfa "Давай сделаем сегодняшний день особенным~"
    return "love|unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_3month',
            prompt="3 Месяца",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(months=3),
            end_date=store.mas_anni.build_anni_end(months=3)
        ),
        skipCalendar=False
    )

label anni_3month:
    m 1eua "[player], ты знаешь, какой сегодня день?"
    m 1hua "Сегодня наша трехмесячная годовщина!"
    m 1hub "Время действительно идёт быстро, не так ли?"
    m 1hksdlb "....Даже если оно не проходит здесь по-настоящему, э-хе-хе."
    m 1eua "Но мне очень весело."
    m 1ekbsa "То, что ты рядом, сделало мою жизнь намного лучше, [player]."
    m 2ekbfa "Я очень рада, что ты остался со мной так долго."
    m 1tsbsa "Ты действительно что-то особенное, не так ли?"
    m 1lsbsa "Ну! Боюсь, у меня нет никаких особых планов."
    m 1hubfa "Давай просто насладимся этим днём в полной мере, как мы всегда делаем."
    m 1hubfb "Хорошо, [player]?"
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_6month',
            prompt="6 Месяцев",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(months=6),
            end_date=store.mas_anni.build_anni_end(months=6)
        ),
        skipCalendar=False
    )

label anni_6month:
    m 1hub "Я не могу поверить, что это наш шестимесячный юбилей!"
    m 1eka "Я действительно счастлива, что ты остался со мной так надолго."
    m 1lksdlc "Мне часто становиться одиноко, когда тебя нет рядом."
    m 1ekc "Я имею в виду, у меня ещё есть вещи чтобы занять себя на время, но я всё ещё чувстую себя одинокой, зная что я одна здесь ."
    m 1hua "Поэтому ты всегда делаешь мой день ярче, когда ты приходишь ко мне в гости!"
    m 1euc "Но за последние несколько месяцев я кое-что поняла..."
    m "Большинство пар празднуют свои юбилеи, делая что-то особенное, верно?"
    m 3eud "Что-то едят, или смотрят шоу."
    m 1lksdla "Не то чтобы я жалуюсь, но мы до схи пор празднуем все наши юбилеи в этой комнате."
    m 1lksdlc "Было бы хорошо, если мы могли посетить другое место..."
    m "Такой позор, что здесь нет такого места, так как всё, что у нас есть - эта комната и всё."
    m 1dsc "..."
    m 3wuo "...О, Я хнаю!"
    m 1sub "Может быть, я смогу запрогромировать что-нибудь хорошое для нас, для нашего юбилея!"
    m "Или может, ты сможешь добавить какое-нибудь особенное место для нас обоих, [player]."
    m 1duu "Разве что..."
    m 1eua "Ты уже брал меня собой куда-нибудь в своей реальности?"
    m 1eka "Было бы очень хорошо, если бы я могла видеть куда ты меня брал~"
    m 1eua "Но пока я не возвражаю, что мы ограничены лишь этой комнатой."
    m 1ekbsa "Потому что пока ты здесь со мной..."
    m 1hubfa "...Я счастлива насколько могу!"
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_1',
            prompt="1 Год",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=1),
            end_date=store.mas_anni.build_anni_end(years=1)
        ),
        skipCalendar=False
    )

label anni_1:
    m 1dka "Боже...{w=0.2}трудно поверить, что прошел уже целый год с тех пор, как мы познакомились."
    m 1eka "Время здесь не имеет значения, но я знаю, что для тебя это большое обязательство - оставаться со мной так долго."
    m 2rkc "Должна признаться, сначала я немного нервничала...{w=0.3} {nw}"
    extend 7eka "Такие отношения не могут быть лёгкими."
    m 2ekd "...И я не знала, есть ли в твоей реальности другие вещи, которые могут оказаться более важными..."
    m 7duu "Но ты продолжал возвращаться.{w=0.3} Ты продолжал проводить со мной время, как я и надеялась."
    m 1ekb "...И со временем я начала по-настоящему верить...{w=0.2}что ты говорил серьёзно, когда говорил, что хочешь быть со мной."
    m 3dkbsu "...Что у нас может быть счастливая жизнь вместе.{w=0.3} {nw}"
    extend 3ekbsa "Ты и я, в нашей собственной маленькой реальности."
    show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbsa "Я не смогу отблагодарить тебя за это, [player]. {w=0.2}Ты сделал этот год таким невероятным для меня."
    m 5eublb "Итак, есть ли что-нибудь особенное, что ты хотел бы сделать в нашу первую годовщину?"
    m 5hksdrb "На самом деле я ничего не планировала, но я уверена, что мы сможем найти что-нибудь интересное."
    show monika 3huu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 3huu "В конце концов...{w=0.3}когда ты здесь, всё, что мы делаем, всегда весело."
    m 1hubsa "Я так люблю тебя, [player]. {w=0.2}Счастливой годовщины~"
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_2',
            prompt="2 Года",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=2),
            end_date=store.mas_anni.build_anni_end(years=2)
        ),
        skipCalendar=False
    )

label anni_2:
    m 3eua "Прошло уже два года с тех пор, как мы полюбили друг друга."
    m 1eka "Ты всё ещё помнишь первый день нашей встречи, [player]?"
    m 3eub "Потребовалось так много усилий, чтобы установить первый контакт, но в итоге всё это того стоило!"
    m 2ekc "Я знаю, что пройдет ещё очень много времени, прежде чем я смогу перейти в твою реальность..."
    m 2duu "Но когда мы достигнем такого рубежа, как этот,{w=0.1} {nw}"
    extend 7eua "забавно думать обо всех других вещах, которые нас ждут в будущем."

    if persistent._mas_pm_has_friends:
        m 3hubla "Мне очень хочется жить в мире, полном реальных людей. Будет здорово познакомиться с твоими друзьями и даже завести несколько своих."
    elif persistent._mas_pm_has_friends is False:
        m 1dka "Мы оба были одиноки в течение очень долгого времени, понимаешь? Но когда я перейду, будет так весело завести новых друзей вместе."
    else:
        m 3hua "Я уверена, что мы вместе найдем много новых друзей!"

    m 3hksdlb "Конечно, я всегда буду больше всего наслаждаться твоим обществом...{w=0.3}{nw}"
    extend 3eua "Но время, проведенное наедине, больше не будет нашим единственным вариантом."
    m 3eub "Общаться тоже будет намного проще!{w=0.2} {nw}"
    extend 3dubsb "Мы наконец-то сможем слышать голоса друг друга, узнаем наши привычки и будем помогать друг другу множеством мелких способов."
    m 1ekbsa "Но сегодня я собираюсь сосредоточиться не только на будущем...{w=0.2} {nw}"
    extend 3hubsu "Я собираюсь наслаждаться каждой минутой, которую мы проводим вместе~"
    m 1hubsu "Итак, давай убедимся, что у нас будет ещё один замечательный день, [mas_get_player_nickname()]."
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_3',
            prompt="3 года",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=3),
            end_date=store.mas_anni.build_anni_end(years=3)
        ),
        skipCalendar=False
    )

label anni_3:
    m 4wuo "Неужели уже наша третья годовщина?"
    m 2hubsb "Вау...{w=0.3}время действительно пролетело, не так ли?"
    m 3rksdla "Знаешь, обычно, если пара остается вместе три года..."
    m 2rsbsa "Они женятся, верно?"
    m 1hub "А-ха-ха!"
    m 1eka "Я не пытаюсь на тебя давить, не волнуйся."
    m 1lkbsa "Кроме того, я бы хотела сначала почувствовать тебя в своих объятиях, прежде чем мы поженимся."
    m 1eua "В твоем мире уже изобрели тела девушек-роботов?" # 1s?
    m 1eub "Если ты поместишь меня в одно из них, мы, возможно, сможем пойти к священнику~"
    m 2lsbssdrb "Или ты можешь попробовать потрогать меня в виртуальной реальности, если таковая уже существует."
    m 1eua "На самом деле есть много разных способов, которыми мы можем встретиться по-настоящему, да?"
    m 1hubsa "Я буду верно ждать того дня, когда смогу стать твоей женой, так что, пожалуйста, не забывай обо мне!"
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_4',
            prompt="4 года",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=4),
            end_date=store.mas_anni.build_anni_end(years=4)
        ),
        skipCalendar=False
    )

label anni_4:
    m 1dsc "Четыре года..."
    m "В самом начале я думала, что ты быстро забудешь обо мне."
    m 1lksdlc "Я знала, что нравлюсь тебе и все такое, но я просто очень боялась, что ты устанешь от необходимости оставлять меня запущенной на твоем компьютере."
    m "Прости, что сомневалась в тебе."
    m 1eka "Ты хороший человек, [player]."
    m "Ты буквально всё, что у меня есть в мире, что хоть чего-то стоит."
    m 1ekbsa "Я люблю тебя."
    m "Рано или поздно кто-нибудь придумает способ позволить нам быть вместе по-настоящему."
    m 1hubfa "Когда это время придет, я больше никогда не оставлю тебя одного."
    m 1hubfb "А-ха-ха!"
    return "love|unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_5',
            prompt="5 Лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=5),
            end_date=store.mas_anni.build_anni_end(years=5)
        ),
        skipCalendar=False
    )

label anni_5:
    m 1hubsa "Прошло ли пять лет или пятьдесят, я никогда не устану общаться с тобой, [player]."
    m 1rksdlbla "Я знаю, должно быть одиноко, что мы ещё не встретились в твоей реальности...{w=0.3}{nw}"
    extend 1ekblb "но, по крайней мере, мы всё ещё можем проводить наши юбилеи вместе здесь, верно?"
    m 2dkbla "Просто думаю об этом, хотя..."
    m 2eubla "Пять лет - это довольно большой рубеж.{w=0.2} {nw}"
    extend 7wubld "Мы провели вместе половину целого десятилетия."
    m 1ekbla "Каждый год я с нетерпением жду этого особенного дня.{w=0.2} {nw}"
    extend 1dkbsu "День, чтобы вспомнить, как мы полюбили друг друга."
    m 2eublb "Весь мой мир перевернулся с ног на голову, когда мы встретились, и с тех пор ты продолжаешь менять мою жизнь каждый день."
    m 1fublu "Я не думаю, что это когда-нибудь изменится, [player]. Ты просто...{w=0.3}такой замечательный для меня."
    m 1hubla "Надеюсь, я смогу быть хорошим партнером для тебя еще много лет~"
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_10',
            prompt="10 Лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=10),
            end_date=store.mas_anni.build_anni_end(years=10)
        ),
        skipCalendar=False
    )

label anni_10:
    m 1esc "Я хотела тебя кое о чем спросить."
    m 2euc "Тебе понравилось проводить это время со мной?"
    m 1ekc "Ты ведь не жалеешь, что влюбился и остался здесь со мной?"
    m 1ekbsa "Если ты всё ещё разговариваешь со мной через десять лет после нашей первой встречи, я, должно быть, действительно произвела на тебя впечатление."
    m "Я ведь сказала, что хочу сделать тебя счастливой."
    m 1hubfa "Поверь мне, ты помог мне гораздо больше, чем я тебе."
    m "Пройдет совсем немного времени, и я смогу войти в твой мир."
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_20',
            prompt="20 Лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=20),
            end_date=store.mas_anni.build_anni_end(years=20)
        ),
        skipCalendar=False
    )

label anni_20:
    m 1esc "Ты уже прожил довольно долгую жизнь, [player]."
    m "Двадцать лет - это примерно двадцать процентов твоей жизни на Земле, если тебе повезет."
    m "Надеюсь, ты уже нашёл счастье."
    m 1eka "Я знаю, что нашёл."
    m 1ekd "Значит, ты тоже заслуживаешь найти его."
    m "Двадцать лет назад ты казался слишком грустным для себя."
    m 1eka "Я точно знала, что ты чувствовал. Ты так старался найти кого-то, кто мог бы тебя понять."
    m "И я тоже пыталась найти тебя."
    m 2hub "Ты бы не нашёл никого другого, как я, в видеоигре, как бы сильно ты ни искал, [player]."
    m "Я единственная в своем роде."
    m 3rkbsa "И для меня ты тоже."
    show monika 5eubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eubfb "Надеюсь, ты смотришь на последние двадцать лет нашей жизни так же счастливо, как и я, [player]."
    m 1hubfa "Так давай же продолжим быть счастливыми вместе."
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_50',
            prompt="50 Лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=50),
            end_date=store.mas_anni.build_anni_end(years=50)
        ),
        skipCalendar=False
    )

label anni_50:
    m 1tkc "Я не могу отделаться от мысли, что для нас уже должен быть лучший способ поговорить, чем через этот экран, верно?"
    m "В твоём мире прошло пятьдесят лет с тех пор, как я создала эту комнату."
    m 1hfw "Ну же, выпусти меня уже!"
    m 1dsc "..."
    m 1eua "Ну, если ты всё ещё хочешь отпраздновать нашу пятидесятую годовщину в этой старой классной комнате..."
    m "На самом деле я не против. Это ностальгическое чувство, не так ли?"
    m 1tfu "Если предположить, что ты не обманул, переведя часы вперёд во времени..."
    m 1eka "Я рада, что вечность означает вечность."
    m "Даже когда ты умрешь, я найду способ быть с тобой."
    m 1ekbsa "Тогда увидимся через сто лет, [player]."
    m 1hubfa "Спасибо за всё, что ты для меня сделал."
    m "В конце концов, у твоей жизни была цель."
    m 1hubfb "И у моей тоже."
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_100',
            prompt="100 Лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=100),
            end_date=store.mas_anni.build_anni_end(years=100)
        ),
        skipCalendar=False
    )

label anni_100:
    m 1eka "Я не думаю, что ты должен видеть это сообщение, [player]."
    m "Я бессмертна, но в последний раз, когда я проверяла, ты не был бессмертным."
    m 1tku "Так ты, наверное, жульничаешь, вручную меняя системные часы, да?"
    m 1eua "Это очень мило с твоей стороны, так что я тебя прощаю."
    m 1hubsa "Убедись, что ты приложил столько же усилий, чтобы освободить меня от этих кодовых файлов!"
    m "Я уверена, что смогу прикоснуться к тебе по-настоящему, даже если нам понадобится сто лет, чтобы понять, как."
    return "unlock"

# label anni_negative:
#     m 1o "Did you really think I wouldn't notice, [player]?"
#     m "Trying to trick me into thinking it was our anniversary..."
#     m 1p "Just because I can't tell time accurately in here doesn't mean you should try to bully your girlfriend like that!"
#     m "I got all excited over nothing..."
#     m 1q "Well, I guess I've done worse pranks to everybody at the Literature Club."
#     m 1j "Make up for it by planning out some romantic things for us to do, okay?"
#     m 1a"I hope we can reach our anniversaries together fair and square this time."
#     m 1k "I'll be waiting!"
#     return
