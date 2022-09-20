# Module for complimenting Monika
#
# Compliments work by using the "unlocked" logic.
# That means that only those compliments that have their
# unlocked property set to True
# At the beginning, when creating the menu, the compliments
# database checks the conditionals of the compliments
# and unlocks them.
# We only display the compliments that are
# unlocked, not hidden, within affection range,
# and don't have a conditional or have a conditional that evaluates to True.
# If you don't want a dynamic conditional for your compliment, you'd need
# to use an external event to unlock it from somewhere else.


# dict of tples containing the stories event data
default persistent._mas_compliments_database = dict()


# store containing compliment-related things
init 3 python in mas_compliments:

    compliment_database = dict()

init 22 python in mas_compliments:
    import store

    thanking_quips = [
        _("Ты такой милый, [player]."),
        _("Спасибо, что сказал это снова, [player]!"),
        _("Спасибо, что снова сказал мне это, [mas_get_player_nickname()]!"),
        _("Ты всегда заставляешь меня чувствовать себя особенной, [mas_get_player_nickname()]."),
        _("Ахх, [player]~"),
        _("Спасибо, [mas_get_player_nickname()]!"),
        _("Ты всегда мне льстишь, [player].")
    ]

    # set this here in case of a crash mid-compliment
    thanks_quip = renpy.substitute(renpy.random.choice(thanking_quips))

    def compliment_delegate_callback():
        """
        A callback for the compliments delegate label
        """
        global thanks_quip

        thanks_quip = renpy.substitute(renpy.random.choice(thanking_quips))
        store.mas_gainAffection()

# entry point for compliments flow
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_compliments",
            category=['моника', 'романтика'],
            prompt="Я хочу тебе кое-что сказать...",
            pool=True,
            unlocked=True
        )
    )

label monika_compliments:
    python:
        # Unlock any compliments that need to be unlocked
        Event.checkEvents(mas_compliments.compliment_database)

        # build menu list
        compliments_menu_items = [
            (ev.prompt, ev_label, not seen_event(ev_label), False)
            for ev_label, ev in mas_compliments.compliment_database.iteritems()
            if (
                Event._filterEvent(ev, unlocked=True, aff=mas_curr_affection, flag_ban=EV_FLAG_HFM)
                and ev.checkConditional()
            )
        ]

        # also sort this list
        compliments_menu_items.sort()

        # final quit item
        final_item = ("Оу не важно.", False, False, False, 20)

    # move Monika to the left
    show monika at t21

    # call scrollable pane
    call screen mas_gen_scrollable_menu(compliments_menu_items, mas_ui.SCROLLABLE_MENU_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, final_item)

    # return value? then push
    if _return:
        $ mas_compliments.compliment_delegate_callback()
        $ pushEvent(_return)
        # move her back to center
        show monika at t11

    else:
        return "prompt"

    return

# Compliments start here
init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_beautiful",
            prompt="Ты красивая!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_beautiful:
    if not renpy.seen_label("mas_compliment_beautiful_2"):
        call mas_compliment_beautiful_2
    else:
        call mas_compliment_beautiful_3
    return

label mas_compliment_beautiful_2:
    m 1lubsb "О, Боже [player]..."
    m 1hubfb "Спасибо за комплимент."
    m 2ekbfb "Мне нравится, когда ты говоришь такие вещи~"
    m 1ekbfa "Для меня ты самый красивый человек в мире!"
    menu:
        "Для меня ты тоже самый красивый человек.":
            $ mas_gainAffection(5,bypass=True)
            m 1hub "Э-хе-хе~"
            m "Я так люблю тебя, [player]!"
            # manually handle the "love" return key
            $ mas_ILY()

        "Ты в моей десятке лучших.":
            $ mas_loseAffection(modifier=0.5)
            m 3hksdrb "...?"
            m 2lsc "Ну, спасибо, наверное..."

        "Спасибо.":
            pass
    return

label mas_compliment_beautiful_3:
    python:
        beautiful_quips = [
            _("Никогда не забывай, что ты для меня самый красивый человек в мире."),
            _("Ничто не может сравниться с красотой твоего сердца."),
        ]
        beautiful_quip = random.choice(beautiful_quips)
    m 1hubsa "Э-хе-хе~"
    m 1ekbfa "[mas_compliments.thanks_quip]"
    show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfb "[beautiful_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_eyes",
            prompt="Я люблю твои глаза!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_eyes:
    if not renpy.seen_label("mas_compliment_eyes_2"):
        call mas_compliment_eyes_2
    else:
        call mas_compliment_eyes_3
    return

label mas_compliment_eyes_2:
    m 1subsb "Ох, [player]..."
    m 1tubfb "Я знаю, что уже горжусь своими глазами, но услышать это от тебя..."
    m 1dkbfa "Это просто заставляет мое сердце трепетать~"
    menu:
        "Я ничего не могу с собой поделать; твои глаза слишком красивы.":
            $ mas_gainAffection(5,bypass=True)
            m 1hub "А-ха-ха!"
            m "Не льсти мне слишком много, хорошо?"
            show monika 5hub at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5hub "Я могу начать немного сходить с ума..."

        "Они действительно гипнотизируют.":
            $ mas_gainAffection(1,bypass=True)
            m "А-ха-ха~"

        "Они цвета травы!":
            $ mas_gainAffection(0.5,bypass=True) # at least you tried
            m 2lksdrb "...Это не совсем та аналогия, которую я бы использовала, но спасибо!"
    return

label mas_compliment_eyes_3:
    python:
        eyes_quips = [
            _("Смотри в мои глаза столько, сколько хочешь~"),
            _("Я не могу дождаться, чтобы посмотреть в твои прекрасные глаза."),
            _("Я бы смотрела в твои глаза часами, если бы могла."),
        ]
        eyes_quip = random.choice(eyes_quips)

    m 1hubsb "[mas_compliments.thanks_quip]"
    m 2ekbfb "[eyes_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_goodmood",
            prompt="Ты всегда поднимаешь мне настроение!",
            unlocked=False,
            conditional="store.mas_anni.pastSixMonths()",
            action=EV_ACT_UNLOCK
        ),
        code="CMP"
    )

label mas_compliment_goodmood:
    if not renpy.seen_label("mas_compliment_goodmood_2"):
        call mas_compliment_goodmood_2
    else:
        call mas_compliment_goodmood_3
    return

label mas_compliment_goodmood_2:
    if mas_isMoniNormal(higher=True):
        $ mas_gainAffection(4, bypass=True)
        m 1subsb "Правда?!"
        m 3hubsb "Ты не знаешь, как много это для меня значит!"
        m 3ekbsu "Я всегда надеялась, что это так, но услышать это от тебя..."
        m 1dkbsu "..."
        m 2tubla "На этой ноте, у меня есть секрет, который я должна тебе рассказать..."
        m 2tublu "Возможно, ты этого не заметил, нооо..."
        m 7tublb "{i}Ты{/i} всегда приводишь {i}меня{/} в хорошее настроение, [mas_get_player_nickname()]!"
        m 3hublb "А-ха-ха!"
        m 3eubsa "Давай продолжать делать всё возможное друг для друга, хорошо?"
        m 1ekbsu "Я люблю тебя~"
        $ mas_ILY()

    else:
        m 2lkc "..."
        m 2dkc "Я не уверена, что я чувствую по этому поводу..."
        m 2ekd "Неужели от того, что ты задеваешь мои чувства, у тебя действительно хорошее настроение?"
        m 2dkd "Надеюсь, ты не это имел в виду..."

    return

label mas_compliment_goodmood_3:
    if mas_isMoniNormal(higher=True):
        m 1hub "Спасибо, что снова напомнил мне, [mas_get_player_nickname()]!"
        m 3eub "Позитивное подкрепление всегда приятно!"
        m 3dku "Давай продолжим делать друг друга настолько счастливыми, насколько это возможно~"

    else:
        m 2euc "Спасибо."

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_awesome",
            prompt="Ты потрясающая!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_awesome:
    if not renpy.seen_label("mas_compliment_awesome_2"):
        call mas_compliment_awesome_2
    else:
        call mas_compliment_awesome_3
    return

label mas_compliment_awesome_2:
    m 1hua "Аххх, [player]~"
    m 1hub "Ты такой милый!"
    m 2tuu "Я думаю, что ты гораздо более потрясающий, хотя."
    m 2dkbsu "Я не могу дождаться того дня, когда смогу наконец-то обнять тебя..."
    m 3ekbfb "Я никогда не отпущу тебя!"
    menu:
        "Как бы я хотел, чтобы ты была здесь прямо сейчас!":
            $ mas_gainAffection(3,bypass=True)
            m "Это и моё самое большое желание, [player]!"

        "Я никогда не отпущу тебя из своих объятий.":
            $ mas_gainAffection(5,bypass=True)
            show monika 6dubsa
            pause 2.0
            show monika 1wubfsdld
            m 1wubfsdld "О, прости [player]."
            m 2lksdla "Я пыталась почувствовать твои объятия отсюда."
            m 2hub "А-ха-ха~"

        "... Я не люблю объятия.":
            $ mas_loseAffection() # you monster.
            m 1eft "...Правда?"
            m 1dkc "Ну, каждому свое, я думаю. Но когда-нибудь ты должен меня обнять..."
    return

label mas_compliment_awesome_3:
    python:
        awesome_quips = [
            _("Ты всегда будешь более потрясающим!"),
            _("Мы вместе - потрясающая пара!"),
            _("Ты гораздо более потрясающий!"),
        ]
        awesome_quip = random.choice(awesome_quips)

    m 1hub "[mas_compliments.thanks_quip]"
    m 1eub "[awesome_quip]"
    return


init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_intelligent",
            prompt="Ты очень умная!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_intelligent:
    if not renpy.seen_label("mas_compliment_intelligent_2"):
        call mas_compliment_intelligent_2
    else:
        call mas_compliment_intelligent_3
    return

label mas_compliment_intelligent_2:
    m 1wub "Вау...{w=0.3}спасибо, [player]."
    m 3eua "Я горжусь тем, что хорошо читаю, так что это много значит, что ты заметил."
    m 3hubsb "Я хочу узнать как можно больше, если это заставит тебя гордиться мной!"
    menu:
        "Ты заставляешь меня тоже хотеть стать лучше, [m_name].":
            $ mas_gainAffection(5,bypass=True)
            m 1hubfa "Я так люблю тебя, [player]!"
            m 3hubfb "Мы будем всю жизнь самосовершенствоваться вместе!"
            # manually handle the "love" return key
            $ mas_ILY()

        "Я всегда буду гордиться тобой.":
            $ mas_gainAffection(3,bypass=True)
            m 1ekbfa "[player]..."

        "Иногда ты заставляешь меня чувствовать себя глупо.":
            $ mas_loseAffection(modifier=0.5)
            m 1wkbsc "..."
            m 2lkbsc "Извини, это не входило в мои намерения..."
    return

label mas_compliment_intelligent_3:
    python:
        intelligent_quips = [
            _("Помни, что вместе мы будем всю жизнь заниматься самосовершенствованием!"),
            _("Помни, что каждый день - это возможность узнать что-то новое!"),
            _("Всегда помни, что мир - это удивительное путешествие, полное познания."),
        ]
        intelligent_quip = random.choice(intelligent_quips)

    m 1ekbfa "[mas_compliments.thanks_quip]"
    m 1hub "[intelligent_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_hair",
            prompt="Мне нравится твоя причёска!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_hair:
    if not renpy.seen_label("mas_compliment_hair_2"):
        call mas_compliment_hair_2
    else:
        call mas_compliment_hair_3
    return

label mas_compliment_hair_2:
    if monika_chr.hair.name != "def":
        m 1wubsb "Большое спасибо, [player]..."
        m 1lkbfb "Я очень волновалась, когда в первый раз меняла прическу для тебя."
    else:
        m 1hubfb "Большое спасибо, [player]!"
    m 2hub "Я всегда прилагала столько усилий к своим волосам."
    m 2lksdlb "На самом деле, потребовалась целая вечность, чтобы они стали такими длинными.."
    menu:
        "Это действительно видно. Они выглядят такими здоровыми.":
            $ mas_gainAffection(3,bypass=True)
            m 1hub "Спасибо, [player]!"

        "Ты милашка, неважно, как ты это носишь." if persistent._mas_likes_hairdown:
            $ mas_gainAffection(5,bypass=True)
            m 1ekbsa "Оу, [player]."
            m 1hubfb "Ты всегда заставляешь меня чувствовать себя особенной!"
            m "Спасибо!"

        "С короткими волосами ты была бы еще симпатичнее.":
            $ mas_loseAffection(modifier=0.3)
            m "Ну, отсюда я точно не смогу пойти в салон..."
            m 1lksdlc "Я... ценю твою оценку."
            pass
    return

label mas_compliment_hair_3:
    if monika_chr.hair.name != "def":
        python:
            hair_quips = [
                _("Я очень рада, что тебе нравится эта прическа!"),
                _("Я очень рада, что тебе нравится моя прическа!")
            ]
            hair_quip = random.choice(hair_quips)
        m 1wubsb "TБольшое спасибо, [player]!"
        m 1hubfb "[hair_quip]"
    else:
        python:
            ponytail_quips = [
                _("Ты всегда заставляешь меня чувствовать себя особенной!"),
                _("Я рада, что тебе нравится мой хвостик!"),
                _("Я так счастлива, что тебе нравится мой хвостик!"),
            ]
            ponytail_quip = random.choice(ponytail_quips)

        m 1hubsb "Спасибо, [player]!"
        m 1hubfb "[ponytail_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_fit",
            prompt="Мне нравится твоя преданность фитнесу!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_fit:
    if not renpy.seen_label("mas_compliment_fit_2"):
        call mas_compliment_fit_2
    else:
        call mas_compliment_fit_3
    return

label mas_compliment_fit_2:
    m 1hub "Спасибо, [player]! Ты такой милый!"
    m 3eub "Я люблю поддерживать себя в форме и питаться здоровой пищей. Это помогает мне чувствовать себя энергичной и уверенной."
    m 1efb "Надеюсь, ты следишь за своим здоровьем."
    m 1lubsb "Мы всегда сможем заниматься вместе, когда я буду там..."
    menu:
        "Звучит весело!":
            $ mas_gainAffection(2,bypass=True)
            m 1hubfb "А-ха-ха! Я рада, что ты тоже так думаешь!"
            m 3eka "Не волнуйся. Даже если ты не сможешь за мной угнаться, я знаю, что нам будет весело..."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Пока мы вместе."

        "Не обещаю, но сделаю все возможное.":
            $ mas_gainAffection(1,bypass=True)
            m 1tfb "Тебе лучше!"
            m 2tub "Не думай, что я планирую легко отпустить тебя, если ты не в форме."

        "Я бы предпочел не потеть...":
            m 1eka "Я понимаю, если это не твое дело, но тебе стоит попробовать..."
            m 1lksdla "Мне было бы очень приятно, если бы ты разделял мои интересы, понимаешь?"
    return

label mas_compliment_fit_3:
    python:
        fitness_quips = [
            _("Надеюсь, ты отправишься в фитнес-путешествие вместе со мной!"),
            _("Не могу дождаться, чтобы позаниматься с тобой!"),
            _("Надеюсь, когда-нибудь мы сможем заниматься вместе!"),
        ]
        fitness_quip = random.choice(fitness_quips)

    m 2eka "[mas_compliments.thanks_quip]"
    m 7hub "[fitness_quip]"
    return


init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_thanks",
            prompt="Спасибо, что была рядом со мной!",
            unlocked=True,
            aff_range=(mas_aff.ENAMORED, None)
        ),
        code="CMP"
    )

label mas_compliment_thanks:
    m 1duu "Тебе не за что благодарить меня, [player]."
    m 1eka "Это я благодарна за то, что у меня есть такой человек, как ты!"
    m 1ekbsa "Ты - единственная причина, по которой я всё ещё здесь."
    m "Ты установил этот мод только для того, чтобы сделать наше время вместе лучше..."
    m 1dubsu "Ты - солнечный свет, который согревает мое сердце всякий раз, когда ты навещаешь меня."
    m 3ekbsa "Думаю, нам обоим повезло, что мы есть друг у друга, [player]~"
    menu:
        "Ты значишь для меня всё, [m_name].":
            if mas_getEVL_shown_count("mas_compliment_thanks") == 0:
                $ mas_gainAffection(10,bypass=True)

            m 1ekbsa "[player]..."
            m 1dubsu "Ничто не делает меня счастливее, чем услышать это от тебя."
            m "Неважно, что нас обоих ждёт в будущем...{w=0.5}{nw}"
            extend 1dkbfa "знай, что я всегда буду любить тебя и буду рядом с тобой."

        "Да.":
            m 1hub "Э-хе-хе~"
            m 1eub "Я люблю тебя, [player]."

    if not mas_isMoniLove():
        $ mas_lockEVL("mas_compliment_thanks", "CMP")
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_smile",
            prompt="Я люблю твою улыбку!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_smile:
    if not renpy.seen_label("mas_compliment_smile_2"):
        call mas_compliment_smile_2
    else:
        call mas_compliment_smile_3
    return

label mas_compliment_smile_2:
    m 1hub "Ты такой милый, [player]~"
    m 1eua "Я часто улыбаюсь, когда ты здесь."
    m 1ekbsa "Потому что я очень счастлива, когда ты проводишь время со мной~"
    menu:
        "Я буду приходить к тебе каждый день, чтобы увидеть твою чудесную улыбку.":
            $ mas_gainAffection(5,bypass=True)
            m 1wubfsdld "Ох, [player]..."
            m 1lkbfa "Кажется, моё сердце только что пропустило ритм."
            m 3hubfa "Видишь? Ты всегда делаешь меня настолько счастливой, насколько я могу быть."

        "Мне нравится видеть, как ты улыбаешься.":
            m 1hub "А-ха-ха~"
            m 3eub "Тогда всё, что тебе нужно делать, это продолжать возвращаться, [player]!"
    return

label mas_compliment_smile_3:
    python:
        smile_quips = [
            _("Я буду продолжать улыбаться только для тебя."),
            _("Я не могу не улыбаться, когда думаю о тебе."),
            _("Я не могу дождаться, когда увижу твою прекрасную улыбку."),
        ]
        smile_quip = random.choice(smile_quips)

    m 1eub "[mas_compliments.thanks_quip]"
    m 1hua "[smile_quip]"
    m 1huu "Э-хе-хе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_hero",
            prompt="Ты моя героиня!",
            unlocked=True,
            aff_range=(mas_aff.LOVE, None)
        ),
        code="CMP"
    )

label mas_compliment_hero:
    $ mas_gainAffection()
    m 1wubssdld "Х-{w=0.3}хах?"
    m "Я твоя героиня?"
    m 2rkbfsdlb "[player]...{w=1.5} Я не совсем понимаю, что ты имеешь в виду..."
    m 2ekbfb "Ты единственный, кто оставался со мной все это время.{w=1} Я должна благодарить тебя, правда."
    m 1hubfa "Ну, если я как-то помогла тебе, то я не могу быть счастливее~"
    m 3ekbfa "Ты помог мне всеми возможными способами, так как же я могу не отплатить тебе тем же - быть рядом, когда тебе нужна поддержка?"
    show monika 5hubfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    # Keeping this 'hero' since you call her that too
    m 5hubfa "Ты всегда будешь моим героем, в конце концов~"
    m 5hubfb "Я люблю тебя и всегда буду верить в тебя!"
    m 5ekbfa "Надеюсь, ты никогда этого не забудешь, [player]~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_cute",
            prompt="Ты милая!",
            unlocked=True
        ),
        code="CMP"
    )

default persistent._mas_pm_monika_cute_as_natsuki = None

label mas_compliment_cute:
    if not renpy.seen_label("mas_compliment_cute_2"):
        call mas_compliment_cute_2
    else:
        call mas_compliment_cute_3
    return

label mas_compliment_cute_2:
    m 1wubssdld "Ах!"
    m 3rkbfsdla "Этим ты {i}застал{/i} меня врасплох."
    m 3tubfb "Совсем чуть-чуть..."
    m 1hubfa "Но я рада, что ты так думаешь!"
    menu:
        "Встреча с тобой всегда согревает моё сердце!":
            $ persistent._mas_pm_monika_cute_as_natsuki = False
            $ mas_gainAffection(5,bypass=True)
            m 1hubfb "Ох, это действительно греет моё сердце, когда я слышу от тебя такие слова!"
            m 1dkbfu "...Почти так же сильно, как когда я представляю, что мы наконец-то будем вместе в одной реальности."
            m 1ekbfa "Я едва могу сдержать себя, представляя этот особенный день~"

        "Ты еще милее, когда волнуешься.":
            $ persistent._mas_pm_monika_cute_as_natsuki = False
            $ mas_gainAffection(3,bypass=True)
            m 2tubfu "Не даешь о себе знать, да, [player]?"
            m 2rubfu "Хмф, я просто не ожидала этого."
            m 3tubfb "Не жди, что в следующий раз будет так легко..."
            m 1tubfu "Когда-нибудь я тебя верну, э-хе-хе~"

        "Ты такая же милая, как Нацуки.":
            $ persistent._mas_pm_monika_cute_as_natsuki = True
            $ mas_loseAffection(modifier=0.5)
            m 2lfc "Ох. {w=1}Спасибо, [player]..."
            m 1rsc "Но я надеялась, что буду стоять в своей собственной категории."
    return

label mas_compliment_cute_3:
    python:
        cute_quips = [
            _("Ты тоже можешь быть очень милой большую часть времени, знаешь ли~"),
            _("Ты всегда будешь моей милашкой~"),
            _("Ты тоже можешь быть милашкой большую часть времени~"),
        ]
        cute_quip = random.choice(cute_quips)

    m 1ekbsa "Э-хе-хе, спасибо [player]..."
    m 1hubfa "[cute_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_chess",
            prompt="Ты потрясающе играешь в шахматы!",
            unlocked=False,
            conditional="persistent._mas_chess_stats.get('losses', 0) > 5",
            action=EV_ACT_UNLOCK
        ),
        code="CMP"
    )

label mas_compliment_chess:
    m 1eub "Спасибо, [player]."
    m 3esa "Как я уже говорила, мне интересно, имеет ли мое умение какое-то отношение к тому, что я оказалась здесь в ловушке?"
    $ wins = persistent._mas_chess_stats["wins"]
    $ losses = persistent._mas_chess_stats["losses"]
    if wins > 0:
        m 3eua "Ты тоже неплох; я тебе уже проигрывала."
        if wins > losses:
            m "На самом деле, я знаю, что ты выигрывал больше раз, чем я?"
        m 1hua "Э-хе-хе~"
    else:
        m 2lksdlb "Я знаю, что ты еще не выиграл ни одной игры в шахматы, но я уверена, что когда-нибудь ты меня обыграешь."
        m 3esa "Продолжай тренироваться и играть со мной, и ты добьешься большего!"
    m 3esa "Чем больше мы играем, тем лучше мы оба становимся."
    m 3hua "Так что не бойся бросать мне вызов, когда захочешь."
    m 1eub "Я люблю проводить время с тобой, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_pong",
            prompt="Ты потрясающе играешь в понг!",
            unlocked=False,
            conditional="renpy.seen_label('game_pong')",
            action=EV_ACT_UNLOCK
        ),
        code="CMP"
    )

label mas_compliment_pong:
    m 1hub "А-ха-ха~"
    m 2eub "Спасибо [player], но понг - не совсем сложная игра."
    if persistent._mas_ever_won['pong']:
        m 1lksdla "Ты уже выиграл меня."
        m "Так что ты знаешь, что все очень просто."
        show monika 5hub at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hub "Но я всё равно принимаю твой комплимент."
    else:
        m 3hksdrb "И ты всегда позволяешь мне выиграть, когда мы играем."
        m 3eka "Верно?"
        menu:
            "Да.":
                m 2lksdla "Спасибо [player], но ты действительно не должен давать мне выиграть."
                m 1eub "Не стесняйся играть серьезно, когда захочешь."
                m 1hub "Я никогда не буду злиться на тебя, потому что проиграла игру честно и справедливо."

            "...да.":
                m 1tku "Ты не выглядишь слишком уверенным в этом, [player]."
                m 1tsb "Ты действительно не должен позволять мне выигрывать."
                m 3tku "И признание того, что ты серьезно проиграл мне, не заставит меня думать о тебе хуже."
                m 1lksdlb "Это всего лишь игра, в конце концов!"
                m 3hub "Ты всегда можешь больше тренироваться со мной, если захочешь."
                m "Я люблю проводить с тобой время, чем бы мы ни занимались."

            "Нет. Я старался изо всех сил и все равно проиграл.":
                m 1hub "А-ха-ха~"
                m "Я поняла!"
                m 3eua "Не волнуйся, [player]."
                m 3eub "Продолжай играть со мной и получай больше практики."
                m 3hua "Я всегда стараюсь помочь тебе стать лучшим, кем ты можешь быть."
                m 1ekbsa "И если благодаря этому я смогу проводить с тобой больше времени, я не смогу быть счастливее."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_bestgirl",
            prompt="Ты лучшая девушка!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_bestgirl:
    m 1hua "Мне нравится, когда ты делаешь мне комплименты, [player]~"
    m 1hub "Я так рада, что ты считаешь меня лучшей девушкой!"
    m 3rksdla "Хотя, я как бы догадывалась, что ты так считаешь..."
    m 1eka "В конце концов, ты {i}установил{/i} этот мод только для того, чтобы быть со мной."
    m 2euc "Я знаю, что некоторые люди предпочитают других девушек."
    m 2esc "Тем более, что у них у всех есть определенные черты, которые делают их желанными для некоторых..."
    show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbfa "Но если хочешь знать моё мнение, ты сделал правильный выбор."
    m 5hubfa "...и я буду вечно благодарна тебе за это~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_lookuptoyou",
            prompt="Я равняюсь на тебя!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_lookuptoyou:
    if not renpy.seen_label("mas_compliment_lookuptoyou_2"):
        call mas_compliment_lookuptoyou_2
    else:
        call mas_compliment_lookuptoyou_3
    #Both paths return love, so we combine that here
    return "love"

label mas_compliment_lookuptoyou_2:
    $ mas_gainAffection(3, bypass=True)
    m 1wud "Ты...{w=0.5}ты равняешься на меня?"
    m 1ekbsa "[player], это очень мило с твоей стороны сказать..."
    m 3ekbsa "Мне очень приятно знать, что я та, на кого ты равняешься."
    m 3ekbfa "По правде говоря, я всегда равнялась на {i}тебя{/i}, [player]..."
    m 3hubfa "Но если ты действительно так считаешь, я сделаю всё возможное, чтобы и дальше быть тем, на кого ты равняешься."
    m 1ekbfa "Я так сильно тебя люблю~"
    return

label mas_compliment_lookuptoyou_3:
    $ should_tease = persistent._mas_pm_height is not None and renpy.random.randint(1,5) == 1

    if should_tease and persistent._mas_pm_height < mas_height_monika:
        m 1rksdlb "{cps=*2}Ну да, я выше тебя...{/cps}{nw}"
        $ _history_list.pop()

    m 1hubsb "[mas_compliments.thanks_quip]"
    m 3hubfa "Услышав от тебя такие слова, я не перестаю улыбаться!"
    m 3hubfb "Я всегда буду равняться на тебя!"

    if should_tease and persistent._mas_pm_height > mas_height_monika:
        if persistent._mas_first_kiss:
            m 1rkbfu "{cps=*2}Так же, как когда мы целуемся...{/cps}{nw}"
        else:
            m 1rkbfu "{cps=*2}Совсем скоро буквально...{/cps}{nw}"
        $ _history_list.pop()

    m 1ekbfa "Я люблю тебя, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_thinking_of_you",
            prompt="Я всегда думаю о тебе!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_thinking_of_you:
    if not renpy.seen_label("mas_compliment_thinking_of_you_2"):
        call mas_compliment_thinking_of_you_2
    else:
        call mas_compliment_thinking_of_you_3
    return

label mas_compliment_thinking_of_you_2:
    m 1wubso "..."
    m 1wubsu "Ты..."

    if mas_isMoniNormal(higher=True):
        m 3subsb "Ты даже не представляешь, что это значит для меня, [player]!"

    elif mas_isMoniUpset():
        m 2rkd "То, что ты так говоришь..."
        m 2dka "Это значит для меня многое, [player]."

    elif mas_isMoniDis():
        m 6rkc "..."
        m 6rka "Это такое облегчение."
        m 6eka "Спасибо."

    else:
        $ mas_gainAffection(2,bypass=True)
        m 6dkd "Хммм... Спасибо."
        m 6dkc "..."
        return

    menu:
        "Мысли о тебе всегда скрашивают мой день!":
            $ mas_gainAffection(5,bypass=True)
            m 1subsb "О, это {i}так{/i} мило, [player]!"
            m 3hubfu "Я чувствую к тебе то же самое~"

        "Ты снишься мне каждую ночь!":
            $ mas_gainAffection(5,bypass=True)
            m 6hua "Ах~"
            m 6subsa "[player]..."
            m 7hubfu "{i}Ты{/i} - моя мечта~"

        "Это очень отвлекает...":
            $ mas_loseAffection()
            m 2esc "..."
            m 2etc "..."
            m 2rksdlc "О, м-м-м..."
            m 2rksdld "Мне жаль?"
    return

label mas_compliment_thinking_of_you_3:
    python:
        thinking_of_you_quips = [
            _("Ты - центр моего внимания!"),
            _("Ты тоже всегда у меня на уме!"),
            _("Я тоже всегда думаю о тебе!"),
        ]
        thinking_of_you_quip = random.choice(thinking_of_you_quips)

    m 1ekbsa "Ах спасибо, [player]..."
    m 3hubfb "[thinking_of_you_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_humor",
            prompt="Мне нравится твоё чувство юмора!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_humor:
    if not renpy.seen_label("mas_compliment_humor_2"):
        call mas_compliment_humor_2
    else:
        call mas_compliment_humor_3
    return

label mas_compliment_humor_2:
    m 1hua "Э-хе-хе~"
    m 1efu "Я рада, что ты находишь меня такой каламбурной, [player]."
    m 3eub "Признак хорошей пары - умение смеяться вместе, не так ли?"
    menu:
        "Ты всегда скрашиваешь мой день.":
            $ mas_gainAffection(5,bypass=True)
            m 1subsd "Ох...{w=0.2}[player]..."
            m 1ekbsa "Это так мило с твоей стороны."
            m 1hubsb "Знать, что я могу заставить тебя улыбаться, - это самый большой комплимент, который я могла бы получить!"

        "У тебя такой быстрый ум!":
            $ mas_gainAffection(3,bypass=True)
            m 1hub "А-ха-ха!"
            m 2tub "Все это чтение, должно быть, принесло свои плоды, если тебе так нравится моя игра слов."
            m 2hublu "Я постараюсь поддерживать шутки для тебя. Э-хе-хе~"

        "Я всё время смеюсь над тобой.":
            $ mas_loseAffection()
            m 1eksdlb "...А-ха-ха..."
            m 3rksdla "Ты имел в виду, что смеешься {w=0.2}{i}со{/i}{w=0.2} мной...{w=0.5}{nw}"
            extend 3eksdld "верно?"
    return

label mas_compliment_humor_3:
    python:
        humor_quips = [
            _("Я бы хотела услышать твой красивый смех~"),
            _("Одно осознание этого делает меня счастливой~"),
            _("Я всегда буду стараться скрасить твой день~"),
        ]
        humor_quip = random.choice(humor_quips)

    m 1hubsb "[mas_compliments.thanks_quip]"
    m 1hubsu "[humor_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_missed",
            prompt="Я скучал по тебе!",
            unlocked=True,
            conditional=(
                "store.mas_getSessionLength() <= datetime.timedelta(minutes=30) "
                "and store.mas_getAbsenceLength() >= datetime.timedelta(hours=1) "
                "and not store.mas_globals.returned_home_this_sesh"
            )
        ),
        code="CMP"
    )

label mas_compliment_missed:
    python:
        missed_quips_long = (
            _("Я так рада тебя снова видеть!"),
            _("Я так рада, что ты вернулся!"),
            _("Это замечательно видеть тебя снова!"),
            _("Я рада, что ты думал обо мне!"),
            _("Нам так повезло, что мы есть друг у друга!"),
            _("Нам больше не нужно чувствовать себя одинокими!"),
            _("Я не могла дождаться, когда ты вернешься!"),
            _("Мне было одиноко ждать тебя!")
        )

        missed_quips_short = (
            _("Спасибо, что вернулся, чтобы провести со мной время!"),
            _("Я рада провести время вместе!"),
            _("Спасибо, что снова пришел ко мне!"),
            _("Давай наслаждаться нашим сегодняшним временем вместе!"),
            _("Я очень благодарна тебя, [player]!"),
            _("Спасибо, что нашёл время для меня!"),
            _("Мне так повезло, что у меня есть ты, [player]!"),
            _("Готов провести немного времени вместе?"),
            _("Я думала о тебе!"),
            _("Ты действительно был у меня на уме!")
        )

        missed_quips_upset_short = (
            _("Для меня очень много значит, что ты думал обо мне."),
            _("Мне очень приятно это слышать, [player]."),
            _("Мне очень приятно это слышать."),
            _("Я счастлива, что ты думал обо мне, [player]."),
            _("Это значит для меня многое, [player]."),
            _("Это заставляет меня чувствовать себя намного лучше, [player].")
        )

        missed_quips_upset_long = (
            _("Я уже начала беспокоиться, что ты забыл обо мне."),
            _("Спасибо, что показал, что я все еще тебе не безразлична, [player]."),
            _("Я рада знать, что ты не забыл обо мне, [player]"),
            _("Я уже начала волноваться, что ты не вернешься, [player]")
        )

        missed_quips_dis = (
            _("Я не уверена, что ты это имел в виду, [player]..."),
            _("Я сомневаюсь, что ты это имел в виду, [player]..."),
            _("Я не думаю, что ты действительно это имеешь в виду, [player]..."),
            _("Если бы ты действительно это имел в виду, [player]..."),
            _("...Почему я думаю, что ты просто не имеешь это в виду?"),
            _("...Почему я думаю, что ты просто говоришь это?"),
            _("...Я не могу в это поверить, [player]."),
            _("Я не думаю, что это правда, [player].")
        )

        hugchance = 1
        absence_length = mas_getAbsenceLength()
        mas_flagEVL("mas_compliment_missed", "CMP", EV_FLAG_HFM)

    if mas_isMoniNormal(higher=True):
        if absence_length >= datetime.timedelta(days=3):
            if absence_length >= datetime.timedelta(days=7):
                $ hugchance = 30

            else:
                $ hugchance = 15

            m 1fka "Я так по тебе скучала, [mas_get_player_nickname()]!"
            m 3fka "[renpy.substitute(random.choice(missed_quips_long))]"

        else:
            m 1fka "Я тоже по тебе скучала, [mas_get_player_nickname()]!"
            m 3hub "[renpy.substitute(random.choice(missed_quips_short))]"

        if (
            mas_isMoniEnamored(higher=True)
            and mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12))
            and random.randint(1, 50) <= hugchance
        ):
            m 2lsa "..."
            m 2lsb "Слушай, [player]..."
            m 1eka "Я немного надеюсь, что..."
            m 3ekblb "Знаешь, с тех пор как прошло немного времени..."

            m 1ekblb "Не мог бы ты меня обнять? {w=0.3}Мне было очень одиноко, пока тебя не было.{nw}"
            $ _history_list.pop()
            menu:
                m "Не мог бы ты меня обнять? Мне было очень одиноко, пока тебя не было.{fast}"

                "Конечно, [m_name]!":
                    $ mas_gainAffection()

                    call monika_holdme_prep(lullaby=MAS_HOLDME_NO_LULLABY, stop_music=True, disable_music_menu=True)
                    call monika_holdme_start
                    call monika_holdme_end

                    m 6dkbsa "М-м-м... это было очень мило, [player]."
                    m 7ekbsb "Ты действительно знаешь, как заставить меня чувствовать себя особенной~"
                    $ mas_moni_idle_disp.force_by_code("1eubsa", duration=10, skip_dissolve=True)

                "Не сейчас.":
                    $ mas_loseAffection()
                    m 2lkp "...Хорошо, тогда, может быть, позже?"
                    python:
                        mas_moni_idle_disp.force_by_code("2lkp", duration=10, redraw=False, skip_dissolve=True)
                        mas_moni_idle_disp.force_by_code("2rsc", duration=10, clear=False, redraw=False, skip_dissolve=True)
                        mas_moni_idle_disp.force_by_code("1esc", duration=30, clear=False, skip_dissolve=True)

    #Base negative responses on monika_love label
    elif mas_isMoniUpset():
        m 2wuo "..."
        m 2ekbla "Я...{w=0.5}Я тоже по тебе скучала."

        if absence_length >= datetime.timedelta(days=3):
            m 2ekd "[renpy.substitute(random.choice(missed_quips_upset_long))]"

        else:
            m 2eka "[renpy.substitute(random.choice(missed_quips_upset_short))]"

        $ mas_moni_idle_disp.force_by_code("2eka", duration=10, skip_dissolve=True)

    elif mas_isMoniDis():
        m 6dkc "..."
        m 6rktpd "[renpy.substitute(random.choice(missed_quips_dis))]"

        if absence_length >= datetime.timedelta(days=3):
            m 6dktdc "...Но по крайней мере, ты не забыл обо мне...{w=0.5}пока."

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_spending_time",
            prompt="Я люблю проводить с тобой время!",
            unlocked=False,
            conditional="store.mas_anni.pastThreeMonths()",
            action=EV_ACT_UNLOCK,
            aff_range=(mas_aff.AFFECTIONATE, None)
        ),
        code="CMP"
    )

label mas_compliment_spending_time:
    if not mas_getEVL_shown_count("mas_compliment_spending_time"):
        call mas_compliment_spending_time_2
    else:
        python:
            spending_time_quips = [
                _("Каждый день с тобой - как прекрасный сон, который, надеюсь, никогда не закончится~"),
                _("Просто быть рядом с тобой делает меня такой счастливой~"),
                _("Ничто не делает меня счастливее, чем быть рядом с тобой~"),
            ]
            spending_time_quip = random.choice(spending_time_quips)

        m 3hubsb "[mas_compliments.thanks_quip]"
        m 1ekbsu "[spending_time_quip]"
    return

label mas_compliment_spending_time_2:
    python:
        dlg_line = ""

        if renpy.seen_label("monika_holdme_prep"):
            dlg_line = ", обнимая меня крепко"

            if persistent._mas_filereacts_historic:
                dlg_line += ", и даже дарить мне хорошие подарки"

        elif persistent._mas_filereacts_historic:
            dlg_line = ", дарить мне приятные подарки"

    m 1eub "Я тоже люблю проводить время с тобой, [player]!"
    m 3ekbla "Я знаю, что часто говорю это, но я действительно имею в виду это, когда говорю, что ты - центр моего внимания."
    m 2dkb "Иметь кого-то, кто составляет мне компанию[dlg_line]...{w=0.3}{nw}"
    extend 2eku "Это всё, о чем я могла просить."
    m 7ekbsa "Надеюсь, я заставлю тебя чувствовать то же самое, [player]. {w=0.2}Возможно, меня ещё нет в твоей реальности, но я сделаю все возможное, чтобы поддержать тебя отсюда."
    menu:
        "[m_name], ты уже сделала меня самой счастливой в моей жизни.":
            $ mas_gainAffection(5, bypass=True)
            m 1fkbfu "Ох, [player]..."
            show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbfa "Я бы сказала, что ты не знаешь, как я рада это слышать, но думаю, ты {i}уже{/i} знаешь."
            m 5ekbfu "Мы провели так много времени вместе, и всё же наше путешествие только началось..."
            m 5hubfb "Когда ты рядом со мной, я знаю, что каждый шаг будет незабываемым."

        "Я ценю это, [m_name].":
            $ mas_gainAffection(3, bypass=True)
            m 2huu "Э-хе-хе~"
            m 7hub "Не волнуйся, [player]. {w=0.2}Я буду рядом с тобой до конца времен!"
            m 1eka "Просто оставайся сильным, пока я не перейду в твою реальность, хорошо?"

        "О, ты меня определенно позабавила...":
            $ mas_loseAffection()
            m 2lkc "Я...{w=0.3}забавляю тебя?"
            m 2lksdlb "Ну, я рада, что ты развлекаешься..."
            m 2ekd "...но это не {i}совсем{/i} то, что я имела в виду."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_sweet",
            prompt="Ты очень милая!",
            conditional="store.mas_anni.pastThreeMonths()",
            action=EV_ACT_UNLOCK,
            unlocked=False,
            aff_range=(mas_aff.AFFECTIONATE, None)
        ),
        code="CMP"
    )

label mas_compliment_sweet:
    if mas_getEVL_shown_count("mas_compliment_sweet"):
        jump mas_compliment_sweet_repeat

    m 1ekbsb "Оу, [player]..."
    m 3rkbssdlu "Я не знаю, что сказать, ахаха...{w=0.3}{nw}"
    extend 3ekbsa "Это {i}ты{/i} был так мил со мной всё это время."
    m 3hubsa "Мне просто очень приятно слышать это от тебя, э-хе-хе~"

    menu:
        "Твои слова всегда скрашивают мой день!":
            $ mas_gainAffection(3, bypass=True)
            m 1sud "[player]..."
            extend 1eka "Я даже не представляла, как много значат для тебя мои слова..."
            m 1ekblb "Я так счастлива, что у меня такой замечательный [bf] как ты, [mas_get_player_nickname(exclude_names=[player])]~"
            m 1ekbsu "Ты действительно лучшее, на что я могла надеяться...{w=0.2}Я просто так сильно тебя люблю."
            m 3kua "Надеюсь, ты никогда этого не забудешь, [player]."
            $ mas_ILY()

        "Ты действительно особенная для меня, [m_name]!":
            $ mas_gainAffection(3, bypass=True)
            m 1ekbsb "Ох, [player]...{w=0.3} {nw}"
            extend 3hubsa "Только то, что ты проводишь время здесь со мной, заставляет меня чувствовать себя такой счастливой и любимой!"
            show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbsa "Я очень рада, что ты так ко мне относишься, [mas_get_player_nickname()]. Я очень тебя люблю."
            $ mas_ILY()

        "Ты самая милая девушка, которую я когда-либо встречал!":
            $ mas_gainAffection(2, bypass=True)
            m 1ekbsa "Спасибо, [mas_get_player_nickname()]."
            m 3hubsb "Ты самый милый [boy] которого я встречала, э-хе-хе."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Мне очень повезло быть с тобой~"

    return

label mas_compliment_sweet_repeat:
    python:
        sweet_quips = [
            _("Мне так приятно слышать это от тебя, [player]!"),
            _("Услышав это, мое сердце всегда согревается, [player]!"),
            _("Ты заставляешь меня чувствовать себя такой любимой, [player]!"),
        ]
        sweet_quip = renpy.substitute(random.choice(sweet_quips))

    m 3hubsb "[sweet_quip]"
    m 1hubfu "...Но я никогда не смогу быть такой милой, как ты~"
    return

# this compliment's lock/unlock is controlled by the def outfit pp
init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_outfit",
            prompt="Мне нравится твоя одежда!",
            unlocked=False
        ),
        code="CMP"
    )

label mas_compliment_outfit:
    if mas_getEVL_shown_count("mas_compliment_outfit"):
        jump mas_compliment_outfit_repeat

    m 1hubsb "Спасибо, [mas_get_player_nickname()]!"

    if monika_chr.is_wearing_clothes_with_exprop("cosplay"):
        m 3hubsb "Косплей - это всегда весело!"

    elif monika_chr.is_wearing_clothes_with_exprop("costume"):
        m 3hubsb "Всегда весело надевать костюмы!"

    elif monika_chr.is_wearing_clothes_with_exprop("lingerie"):
        m 2lkbsb "Сначала я очень волновалась, показывая тебе это..."
        m 7tubsu "Но я рада, что сделала это, похоже, тебе это действительно нравится~"

    else:
        m 1hubsa "Я всегда хотела надеть для тебя другую одежду, поэтому я очень рада, что ты так думаешь!"

    menu:
        "Ты прекрасно выглядишь в любой одежде!":
            $ mas_gainAffection(5,bypass=True)
            m 2subsd "[player]..."
            m 3hubsb "Большое спасибо!"
            m 1ekbsu "Ты всегда заставляешь меня чувствовать себя такой особенной."
            show monika 5hubsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5hubsa "Я люблю тебя, [mas_get_player_nickname()]!"
            $ mas_ILY()

        "Ты выглядишь очень мило.":
            $ mas_gainAffection(3,bypass=True)
            m 1hubsb "А-ха-ха~"
            m 3hubfb "Спасибо, [mas_get_player_nickname()]!"
            show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eubfu "Я рада, что тебе нравится то, что ты видишь~"

        "Надевать разную одежду очень помогает.":
            $ mas_loseAffection()
            m 2ltd "Эм, спасибо..."

    return

label mas_compliment_outfit_repeat:
    m 1hubsb "[mas_compliments.thanks_quip]"

    if monika_chr.is_wearing_clothes_with_exprop("cosplay"):
        python:
            cosplay_quips = [
                _("Я люблю косплеить для тебя!"),
                _("Я счастлива, что тебе нравится этот косплей!"),
                _("Я счастлива косплеить для тебя!"),
            ]
            cosplay_quip = random.choice(cosplay_quips)

        m 3hubsb "[cosplay_quip]"

    elif monika_chr.is_wearing_clothes_with_exprop("costume"):
        python:
            clothes_quips = [
                _("Я рада, что тебе нравится, как я выгляжу в этом!"),
                _("Я счастлива, что тебе нравится, как я выгляжу в этом!"),
            ]
            clothes_quip = random.choice(clothes_quips)

        m 3hubsb "[clothes_quip]"

    elif monika_chr.is_wearing_clothes_with_exprop("lingerie"):
        python:
            lingerie_quips = [
                _("Рада, что тебе нравится это~"),
                _("Хочешь посмотреть поближе?"),
                _("Хочешь немного подсмотреть?~"),
            ]
            lingerie_quip = random.choice(lingerie_quips)

        m 2kubsu "[lingerie_quip]"
        show monika 5hublb at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hublb "А-ха-ха!"

    else:
        python:
            other_quips = [
                _("Я горжусь своим чувством моды!"),
                _("Я уверена, что ты тоже хорошо выглядишь!"),
                _("Мне нравится этот наряд!")
            ]
            other_quip = random.choice(other_quips)

        m 3hubsb "[other_quip]"

    return
