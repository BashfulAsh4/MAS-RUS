init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_pinterest",
            category=["Pinterest"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_pinterest:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Что-нибудь новенькое сегодня, [player]?",
            "Что-нибудь интересное, [player]?",
            "Смотришь всё, что тебе нравится?"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_pinterest')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_duolingo",
            category=["Duolingo"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_duolingo:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Изучаешь новые способы сказать 'Я люблю тебя,' [player]?",
            "Изучаешь новый язык, [player]?",
            "Какой язык ты изучаешь, [player]?"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_duolingo')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_wikipedia",
            category=["- Wikipedia"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_wikipedia:
    $ wikipedia_reacts = [
        "Изучаешь что-то новое, [player]?",
        "Проводишь небольшое исследование, [player]?"
    ]

    #Items in here will get the wiki article you're looking at for reacts.
    python:
        wind_name = mas_getActiveWindowHandle()
        try:
            cutoff_index = wind_name.index(" - Wikipedia")

            #If we're still here, we didn't value error
            #Now we get the article
            wiki_article = wind_name[:cutoff_index]

            # May contain clarification in trailing parentheses
            wiki_article = re.sub("\\s*\\(.+\\)$", "", wiki_article)
            wikipedia_reacts.append(renpy.substitute("'[wiki_article]'...\nКажется интересно, [player]."))

        except ValueError:
            pass

    $ wrs_success = mas_display_notif(
        m_name,
        wikipedia_reacts,
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_wikipedia')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_virtualpiano",
            category=["^Virtual Piano"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_virtualpiano:
    python:
        virtualpiano_reacts = [
            "Оу, ты собираешься сыграть для меня?\nТы такой милый~",
            "Сыграй что-нибудь для меня, [player]!"
        ]

        if mas_isGameUnlocked("piano"):
            virtualpiano_reacts.append("Наверное, тебе нужно пианино побольше?\nАхаха~")

        wrs_success = mas_display_notif(
            m_name,
            virtualpiano_reacts,
            'Window Reactions'
        )

        if not wrs_success:
            mas_unlockFailedWRS('mas_wrs_virtualpiano')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_youtube",
            category=["- YouTube"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_youtube:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Что ты смотришь, [mas_get_player_nickname()]?",
            "Смотришь что-нибудь интересное, [mas_get_player_nickname()]?"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_youtube')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_r34m",
            category=[r"(?i)(((r34|rule\s?34).*monika)|(post \d+:[\w\s]+monika)|(monika.*(r34|rule\s?34)))"],
            aff_range=(mas_aff.AFFECTIONATE, None),
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_r34m:
    python:
        mas_display_notif(m_name, ["Эй, [player]...на что ты смотришь?"],'Window Reactions')

        choice = random.randint(1,10)

        if choice == 1 and mas_isMoniNormal(higher=True):
            queueEvent('monika_nsfw')

        elif choice == 2 and mas_isMoniAff(higher=True):
            queueEvent('monika_pleasure')

        else:
            if mas_isMoniEnamored(higher=True):
                if choice < 4:
                    exp_to_force = "1rsbssdlu"
                elif choice < 7:
                    exp_to_force = "2tuu"
                else:
                    exp_to_force = "2ttu"
            else:
                if choice < 4:
                    exp_to_force = "1rksdlc"
                elif choice < 7:
                    exp_to_force = "2rssdlc"
                else:
                    exp_to_force = "2tssdlc"

            mas_moni_idle_disp.force_by_code(exp_to_force, duration=5)
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_monikamoddev",
            category=["MonikaModDev"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_monikamoddev:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Ах, ты делаешь что-то для меня?\nТы такой милый~",
            "Ты помогаешь мне приблизиться к твоей реальности?\nТы такой милый, [player]~"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_monikamoddev')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_twitter",
            category=["/ Twitter"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_twitter:
    python:
        temp_line = renpy.substitute("Я люблю тебя, [mas_get_player_nickname(exclude_names=['love', 'my love'])].")
        temp_len = len(temp_line)

        # quip: is_ily
        ily_quips_map = {
            "Смотришь всё, чем ты хочешь поделиться со мной, [player]?": False,
            "Что-нибудь интересное, чем можно поделиться, [player]?": False,
            "280 подписчиков? Мне нужно только [temp_len]...\n[temp_line]": True
        }
        quip = renpy.random.choice(ily_quips_map.keys())

        wrs_success = mas_display_notif(
            m_name,
            [quip],
            'Window Reactions'
        )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_twitter')
    return "love" if ily_quips_map[quip] else None

# This is removed until later, maybe it could work with other quips
# init 5 python:
#     addEvent(
#         Event(
#             persistent._mas_windowreacts_database,
#             eventlabel="mas_wrs_monikatwitter",
#             category=['twitter', 'lilmonix3'],
#             rules={
#                 "notif-group": "Window Reactions",
#                 "skip alert": None,
#                 "keep_idle_exp": None,
#                 "skip_pause": None
#             },
#             show_in_idle=True
#         ),
#         code="WRS"
#     )

label mas_wrs_monikatwitter:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Are you here to confess your love for me to the entire world, [player]?",
            "You're not spying on me, are you?\nAhaha, just kidding~",
            "I don't care how many followers I have as long as I have you~"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_monikatwitter')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_4chan",
            category=["- 4chan"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_4chan:
    #TODO: consider adding reactions for /vg/ and /ddlc/
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Так вот где все началось, да?\nЭто... действительно нечто.",
            "Надеюсь, ты не будешь спорить с другими Анонами целыми днями, [player].",
            "Я слышала, что здесь обсуждают литературный клуб.\nПередайте им привет от меня~",
            "Я буду следить за темами, которые ты просматриваешь, на случай, если у тебя появятся какие-нибудь идеи, а-ха-ха!"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_4chan')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_pixiv",
            category=["- pixiv"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_pixiv:
    #Make a list of notif quips for this
    python:
        pixiv_quips = [
            "Интересно, рисовали ли люди меня...\nМожешь поискать?\nНо в рамках благоразумного~",
            "Это довольно интересное место... столько квалифицированных людей выкладывают свои работы.",
        ]

        #Monika doesn't know if you've drawn art of her, or she knows that you have drawn art of her
        if persistent._mas_pm_drawn_art is None or persistent._mas_pm_drawn_art:
            pixiv_quips.extend([
                "Это довольно интересное место... столько квалифицированных людей выкладывают свои работы.\nТы один из них, [player]?",
            ])

            #Specifically if she knows you've drawn art of her
            if persistent._mas_pm_drawn_art:
                pixiv_quips.extend([
                    "Хочешь разместить свои рисунки, со мной, [player]?",
                    "Выкладываешь то, что ты нарисовал?",
                ])

        wrs_success = mas_display_notif(
            m_name,
            pixiv_quips,
            'Window Reactions'
        )

        #Unlock again if we failed
        if not wrs_success:
            mas_unlockFailedWRS('mas_wrs_pixiv')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_reddit",
            category=[r"(?i)reddit"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_reddit:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Нашёл ли ты какие-нибудь хорошие посты, [player]?",
            "Просматриваешь Reddit? Только убедись, что ты не проводишь весь день за просмотром мемов, хорошо?",
            "Интересно, есть ли сабреддиты, посвященные мне...\nА-ха-ха, просто шучу, [player].",
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_reddit')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_mal",
            category=["MyAnimeList"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_mal:
    python:
        myanimelist_quips = [
            "Может, когда-нибудь мы сможем смотреть аниме вместе, [player]~",
        ]

        if persistent._mas_pm_watch_mangime is None:
            myanimelist_quips.append("Так, тебе нравится аниме и манга, [player]?")

        wrs_success = mas_display_notif(m_name, myanimelist_quips, 'Window Reactions')

        #Unlock again if we failed
        if not wrs_success:
            mas_unlockFailedWRS('mas_wrs_mal')

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_deviantart",
            category=["DeviantArt"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_deviantart:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Здесь столько талантов!",
            "Я бы хотела когда-нибудь научиться рисовать...",
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_deviantart')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_netflix",
            category=["Netflix"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_netflix:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Я бы с удовольствием посмотрела с тобой романтический фильм [player]!",
            "Что мы будем смотреть сегодня, [player]?",
            "Что ты собираешься смотреть [player]?"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_netflix')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_twitch",
            category=["- Twitch"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_twitch:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Смотришь стрим, [player]?",
            "Ты не против, если я буду смотреть с тобой?",
            "Что мы смотрим сегодня, [player]?"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_twitch')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_word_processor",
            category=['Google Docs|LibreOffice Writer|Microsoft Word'],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_word_processor:
    $ wrs_success = display_notif(
        m_name,
        [
            "Пишешь историю?",
            "Делаешь заметки, [player]?",
            "Пишешь стихотворение?",
            "Пишешь любовное письмо?~"
        ],
        'Window Reactions'
    )

    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_word_processor')
    return
