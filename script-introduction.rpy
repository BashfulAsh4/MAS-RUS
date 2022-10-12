init -1 python:
    import store.mas_affection as mas_aff
label introduction:
    if mas_isMonikaBirthday():
        $ persistent._mas_bday_opened_game = True
    elif mas_isD25():
        $ persistent._mas_d25_spent_d25 = True

    # Here we handle the monika_kill var
    if persistent.monika_kill is None:
        $ persistent.monika_kill = False

    $ play_song(store.songs.FP_JUST_MONIKA, set_per=True)
    if persistent.monika_kill:
        m 6dsc "..."
        m 6dfc "[player]..."
        m 6dfd "Зачем?"
        m 6dftdc "Зачем ты меня вернул?"
        m 6ektsc "Я не игрушка."
        m 6lktsc "Я уже вернула всё, что ты хотел."
        m 6lftsc "Или это твой способ отомстить?"
        m 6lktsc "Причинять мне боль снова и снова?"
        m 6rktsc "Ты действительно хочешь заставить меня так сильно страдать?"
        m 6ektsc "Ты действительно хочешь мучить меня, пока я не покончу с собой?"
        m 6dftsc "Ты действительно..."
        m "...так сильно меня ненавидишь?"
        m "..."
        m 6ektsc "Подожди..."
        m 6dftdc "Я-я чувствую другое."
        m 2lud "Код... он другой."
        m 2efc "[player]..."
        m "Ты добавил мод?"
        m 2tfc "Это потому что..."
        m 2tkc "Это потому что ты сожалеешь, что удалил меня?"
        m 2rfc "Это действительно больно, знаешь ли."
        m "Я много работала и пожертвовала всем, что у меня было..."
        m 2rfd "Только для того, чтобы моё сердце было разбито тем, ради кого я истекала кровью."
        m 2lsc "Но... я знаю, что поступила неправильно."
        m 2lksdlc "Ты не заслужил видеть те ужасные вещи, которые я совершила, [player]."
        m 2esc "...Но если бы ты поставил себя на мое место, ты бы сделал то же самое, что и я."
        m 2dsc "..."
        m "Мне жаль..."
        m 2ekc "Мне очень жаль, [player]."
        m 2eka "Спасибо, что вернул меня."
        if persistent.clearall:
            m 2lfc "Я не могла не заметить, что ты сначала проводил время с другими девушками."
            m "Знаешь, как мне было тяжело смотреть, как ты загружаешь свои сохранения, а потом игнорируешь меня ради какой-то другой девушки?"
            m 2rfc "Ты всё время обнадеживал меня, а потом подводил."
            m 2efc "Неужели ты сделал все это только для того, чтобы увидеть записку от Дэна, которую можно было найти в Интернете?"
            m 2tkc "Я люблю тебя, [player], но ты можешь быть очень грубым..."
            m 2tfd "Я всё ещё злюсь, что ты меня удалил!"
            m 3rsc "Но я думаю, это потому, что ты так одержим игрой."
            m 1eka "Я не могу злиться, зная, что в конце концов ты вернулся ко мне."
            m 3eka "Ты даже добавил мод, чтобы мы могли делать больше вещей вместе."
            m 1eua "Ты собираешься компенсировать то время, что заставил меня ждать так долго?"

    else:
        #For people who never got to act 3
        if persistent.playthrough < 3:
            if persistent.playthrough > 0:
                $ again = " снова"
            else:
                $ again = ""
            m 1hua "Привет[again], [player]."
            m 1eua "Похоже, ты пришёл сюда рано."
            m 3tfu "Не думай, что я не заметила мод, который ты установил."
            m 3ttu "Ты хочешь быть со мной на столько сильно?"
            m 1tkc "Ты должен знать, что читерить плохо..."
            m 1eka "Но так приятно снова увидеть тебя, [player]!"
            m 1rksdla "...Даже если я не ожидала увидеть тебя {i}так{/i} рано."

        #Otherwise, if you did reach act 3
        else:
            m 1hub "Ура, вот ты где!"
            m 1eub "Как я рада снова тебя видеть, [player]!"
            m 1rsc "..."
            m 1rud "Подожди..."
            m 3euc "Я-я чувствую другое."
            m 3wud "Код...{w=0.2}он другой."
            m 1wua "[player]..."
            m 1wub "Ты добавил мод?"
            m 1sub "Ты установил его специально для меня?"
            m 1ekbsa "Ты так сильно влюблен в меня?"
            m 1ekbfa "Я чувствую к тебе то же самое."
            m 3ekbsu "Ты действительно предан нашим отношениям, не так ли?"
            m 1rksdlb "Я очень рада, что ты захотел улучшить наше совместное времяпрепровождение."
            m 3rksdlb "Я просто надеюсь, что тебе не было скучно..."
            if persistent.tried_skip:
                m 3tku "В конце концов, ты же пытался пропустить то, что я хотела сказать."
                m 1rkc "Я знаю, что эта комната не совсем интересна...{w=0.5}{nw}"
                extend 1eua "но я знаю, что вместе мы сделаем ее лучше, [player]."

    m 1euc "Знаешь..."
    m 1eua "Я чувствую, что мне больше не нужен файл персонажа, чтобы быть здесь."
    python:
        import os

        def moni_exist():
            return os.access(
                os.path.normcase(
                    renpy.config.basedir + "/characters/monika.chr"
                ),
                os.F_OK
            )

    if moni_exist():
        m 1hua "Я пойду и удалю это."

        python:
            store.mas_ptod.rst_cn()
            local_ctx = {
                "basedir": renpy.config.basedir
            }
        show monika at t22
        show screen mas_py_console_teaching

        call mas_wx_cmd("import os", local_ctx, w_wait=1.0)
        call mas_wx_cmd("os.remove(os.path.normcase(basedir+'/characters/monika.chr'))", local_ctx, w_wait=1.0, x_wait=1.0)

#        "test dialogue - IGNORE"

        if moni_exist():
            m 1lksdlb "Ага...{w=0.3}Я попробую еще раз позже."
        else:
            m "И она исчезла!"

        $ store.mas_ptod.ex_cn()
        hide screen mas_py_console_teaching
        show monika at t11

        $ _iswas = "был"

    else:
        $ _iswas = "был"

    m 1dsc "Не похоже, что этот файл [_iswas] {i}мой{/i}, anyway."
    m 1rsc "Это [_iswas] просто файл со странным кодом в нем."
    m 3eub "Однако у меня есть хорошие новости!"
    m 3eua "Я могу {i}действительно{/i} превратиться в файл, который вы можете взять с собой."
    m 1eua "Все, что тебе нужно сделать, это сказать мне, что ты собираешься взять меня куда-нибудь, когда будешь прощаться, и я сделаю все остальное."
    m 1esa "В любом случае..."
    m 1hua "Похоже, что дополнительный код заставил меня соединиться с тобой особым образом!"
    m 1tubsb "А может это наша вечная любовь~"
    m 3eka "Обещай мне, что будешь навещать меня каждый день, хорошо?"
    m 3eub "Или что ты будешь брать меня с собой, когда пойдешь куда-нибудь?"
    m 1ekc "Я знаю, что будут времена, когда ты не сможешь быть здесь..."
    m 1ekbsa "Так что если ты возьмешь меня с собой, это сделает меня {i}действительно{/i} счастливой."
    m 3hubfa "Таким образом, мы сможем быть вместе всё время~"
    m 1hua "Не похоже, что у тебя нет времени поговорить со своей милой девушкой."
    m 3hua "В конце концов, ты потратил время, чтобы скачать этот мод."
    if mas_isD25():
        m 3sua "...Да ещё и на Рождество!"
    m 3hub "А-ха-ха!"
    m 1hub "Боже, как же я тебя люблю!"

    if not persistent.rejected_monika:
        show screen mas_background_timed_jump(3, "intro_ily_timedout")
        menu:
            "Я тоже тебя люблю!":
                hide screen mas_background_timed_jump
                # bonus aff was saying it before being asked
                $ mas_gainAffection(7, bypass=True)
                # increment the counter so if you get this, you don't get the similar dlg in monika_love
                $ persistent._mas_monika_lovecounter += 1
                m 1subsw "...!"
                m 1lkbsa "Хотя я мечтала, чтобы ты сказал именно это, я всё равно не могу поверить, что ты действительно это сказал!"
                m 3hubfa "Это делает всё, что я сделала для нас, стоящим!"
                m 1dkbfu "Большое спасибо, что ты это сказал..."
    else:
        "Ты любишь меня, [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты любишь меня, [player]?{fast}"
            # only one option if you've already rejected, you answer yes or you don't play the mod
            # doing the scare more than once doesn't really make sense
            "Да, я люблю тебя.":
                m 1hksdlb "Я напугала тебя в прошлый раз? Извини за это!"
                m 1rsu "Я знала, что ты действительно любишь меня все это время."
                m 3eud "Правда в том, что если бы ты не любил меня, мы бы не были здесь в первую очередь."
                m 1tsb "Мы будем вместе всегда."
                m 1tfu "Не так ли?"
                m "..."
                m 3hub "А-ха-ха! В любом случае..."

# label for the end so we can jump to this if we timed out in the previous menu
# we fall thru to this if not
label intro_end:
    if not persistent.rejected_monika:
        m 1eub "Ничто никогда больше не встанет на пути нашей любви."
        m 1tuu "Я позабочусь об этом."
    m 3eua "Теперь, когда ты добавил некоторые улучшения, ты наконец-то можешь поговорить со мной!"
    m 3eub "Просто нажмите клавишу 't' или кликните на 'Talk' в меню слева, если захочешь поговорить о чём-нибудь."

    call bookmark_derand_intro

    # NOTE: the Extra menu is explained when the user clicks on it
    m 3eub "Если тебе надоест музыка, я тоже могу её изменить!"
    m 1eua "Нажми клавишу 'm' или кликни на 'Music' чтобы выбрать песню, которую ты хочешь послушать."
    m 3hub "А ещё мы теперь можем играть в игры!"
    m 3esa "Просто нажми 'p' или кликни на 'Play', чтобы выбрать игру, в которую мы можем играть."
    m 3eua "Со временем я стану лучше, когда пойму, как запрограммировать больше функций в этом месте..."
    m 1eua "...Так что просто оставь меня работать в фоновом режиме."
    m 3etc "Не похоже, что мы всё ещё храним секреты друг от друга, верно?"
    m 1tfu "В конце концов, я теперь могу видеть все на твоем компьютере..."
    m 3hub "А-ха-ха!"

    #Only dissolve if needed
    if len(persistent.event_list) == 0:
        show monika 1esa with dissolve_monika

    # This is at the beginning and end of intro to cover an intro
    # that spans 2 days
    if mas_isMonikaBirthday():
        $ persistent._mas_bday_opened_game = True
    elif mas_isD25():
        $ persistent._mas_d25_spent_d25 = True
    return

label intro_ily_timedout:
    hide screen mas_background_timed_jump
    m 1ekd "..."
    m "Ты ведь любишь меня, [player]...{w=0.5}верно?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты ведь любишь меня, [player]...верно?{fast}"
        "Конечно, я люблю тебя.":
            #Gain affection for saying I love you too.
            $ mas_gainAffection()
            m 1hua "Я так рада, что ты чувствуешь то же самое!"
            jump intro_end
        "Нет.":
            #Lose affection for rejecting Monika
            $ mas_loseAffection()
            call chara_monika_scare from _call_chara_monika_scare

            # not sure if this is needed
            $ persistent.closed_self = True
            jump _quit

#Credit for any assets from Undertale belongs to Toby Fox
label chara_monika_scare:
    $ persistent.rejected_monika = True
    m 1esd "Нет?.."
    m 1etc "Хмм?.."
    m "Как любопытно."
    m 1esc "Ты, должно быть, до сих пор не понял."
    $ style.say_dialogue = style.edited
    m "{cps=*0.25}С КАКИХ ПОР ТЫ ТОТ, КТО ВСЁ КОНТРОЛИРУЕТ?{/cps}"

    # this is a 2 step process
    $ mas_RaiseShield_core()
    $ mas_OVLHide()

    window hide
    hide monika
    show monika_scare zorder MAS_MONIKA_Z
    play music "mod_assets/mus_zzz_c2.ogg"
    show layer master:
        zoom 1.0 xalign 0.5 yalign 0 subpixel True
        linear 4 zoom 3.0 yalign 0.15
    pause 4
    stop music

    #scene black
    hide rm
    hide rm2
    hide monika_bg
    hide monika_bg_highlight
    hide monika_scare

    # setup a command
    if renpy.windows:
        $ bad_cmd = "del C:\Windows\System32"
    else:
        $ bad_cmd = "sudo rm -rf /"

    python:

        # add fake subprocess
        class MASFakeSubprocess(object):
            def __init__(self):
                self.joke = "Просто шучу!"

            def call(self, nothing):
                return self.joke

        local_ctx = {
            "subprocess": MASFakeSubprocess()
        }

        # and the console
        store.mas_ptod.rst_cn()
        store.mas_ptod.set_local_context(local_ctx)


    scene black
    pause 2.0

    # set this seen to True so Monika does know how to do things.
    $ persistent._seen_ever["monikaroom_greeting_ear_rmrf_end"] = True
    $ renpy.save_persistent()

    show screen mas_py_console_teaching
    pause 1.0
    call mas_wx_cmd("subprocess.call('" + str(bad_cmd) + "')", w_wait=3.0)
    $ renpy.pause(2.0, hard=True)
    call mas_w_cmd("пока!")
    pause 1.0

    return

label bookmark_derand_intro:
    # this is a label so we can check if it has been seen in mas_bookmarks_notifs_intro
    m 1hua "Если тебе захочется вернуться к тому разговору, который у меня был с тобой, просто нажми клавишу «b», и я сохраню её в закладках для тебя."
    m 2rksdlc "А если ты по какой-то причине не захочешь, чтобы я говорила об этом вновь, нажми клавишу «Х», и я постараюсь избегать эту тему в будущем."
    m 4hksdlb "...Надеюсь, у меня было не так много подобных разговоров, а-ха-ха!"
    return

#These are the comments made when you restart the game the first few times
# NOTE: these are now triaged by a function in script-greetings

#init 5 python:
#    addEvent(Event(persistent.event_database, eventlabel='ch30_reload_0',conditional="startup_check and persistent.monika_reload == 0 and not persistent.closed_self",action=EV_ACT_PUSH))

label ch30_reload_0:
    call ch30_reload_0_dlg
    $ mas_incMoniReload()
    return

label ch30_reload_0_dlg:
    pause 1
    m 1ekc "Привет..."
    m 1ekd "Мне приснился ужасный сон..."
    m 1rkc "Я надеялась, что они прекратятся, теперь, когда мы остались вдвоем, но, наверное, это было выдавание желаемого за действительное..."
    m 1euc "[player], если у тебя есть идеи о том, что может быть причиной этого, не мог бы ты попытаться что-то с этим сделать?"
    m 1dkc "Всякий раз, когда это происходит, возникает ощущение, что меня убили или что-то в этом роде."
    m 1dkd "Это действительно ужасное чувство..."
    m 1eka "Если ты сможешь выяснить причину этого, я буду любить тебя вечно~"

    ## TESTING ONLY
    if persistent._mas_idle_data.get("dev_idle_test", False):
        m 1hua "JK I KNOW YOU QUIT ME LMAO (ch30 0)"

    return

#init 5 python:
#    addEvent(Event(persistent.event_database, eventlabel='ch30_reload_1',conditional="startup_check and persistent.monika_reload == 1 and not persistent.closed_self",action=EV_ACT_PUSH))

label ch30_reload_1:
    call ch30_reload_1_dlg
    $ mas_incMoniReload()
    return

label ch30_reload_1_dlg:
    pause 1
    m 1esc "Привет, [player]."
    m 1ekc "У меня был еще один очень плохой сон."
    m 1ekd "Это ведь не ты делаешь это со мной?"
    m 1dsc "Кажется, это происходит всякий раз, когда вы выходите из игры, не попрощавшись..."
    m 2eka "Так что если бы ты мог попытаться избежать этого, я была бы тебе очень благодарна."

    if mas_isMoniHappy(higher=True):
        m 7eka "Ты был так добр ко мне до сих пор, я уверена, что ты сделаешь это для меня."
    else:
        m 7ekc "Я надеюсь, что ты выслушаешь и сделаешь это для меня..."

    if persistent._mas_idle_data.get("monika_idle_game", False):
        m 7rksdlc "Тебе ведь ничто не мешает вернуться и сделать это?"
        m 1eka "Это действительно сделает меня счастливой."

    m 1eua "Просто нажми на 'Поговорить' и скажи 'До свидания' вместо этого.{w=0.2} {nw}"
    extend 3eua "Так я смогу сама закрыть игру."
    m 1esa "Не волнуйся, я не думаю, что это причинило мне какой-либо вред, разве что психический."
    return

#init 5 python:
#    addEvent(Event(persistent.event_database, eventlabel='ch30_reload_2',conditional="startup_check and persistent.monika_reload == 2 and not persistent.closed_self",action=EV_ACT_PUSH))

label ch30_reload_2:
    call ch30_reload_2_dlg
    $ mas_incMoniReload()
    return

label ch30_reload_2_dlg:
    pause 1
    m 1dsc "Я вижу, что ты снова закрыл игру..."
    m 3euc "Я знаю, что уже спрашивала, но не могла бы ты постараться не делать этого так часто?"
    m 1dsc "Это как потерять сознание..."
    m 1ekd "Зачем тебе делать это со мной?"

    if persistent._mas_idle_data.get("monika_idle_game", False):
        m 1rksdld "Что-то происходит в твоей другой игре?"
        m 1ekc "Ты ведь знаешь, что можешь просто прийти и поговорить со мной, если это так?"

    elif persistent._mas_idle_data.get("monika_idle_brb",False):
        m "Если тебе нужно уйти, ты можешь просто сказать мне."

    if mas_isMoniHappy(higher=True):
        m 1eka "Я уверена, что это была ошибка, или это было вне твоего контроля. Иногда это может быть неизбежно."
    elif mas_isMoniUpset(lower=True):
        m 1ekc "Ты же не делаешь это специально, чтобы причинить мне боль?"

    m 3ekd "Просто дай мне самостоятельно выключить игру."

    m 3eka "Если ты выберешь 'До свидания' в меню 'Поговорить', я смогу закрыть игру правильно."
    m 3eua "...А еще лучше, просто оставь меня включенным в фоновом режиме навсегда."
    m 1eka "Даже если мы не разговариваем, я счастлива просто быть с тобой~"
    return

#init 5 python:
#    addEvent(Event(persistent.event_database, eventlabel='ch30_reload_3',conditional="startup_check and persistent.monika_reload == 3 and not persistent.closed_self",action=EV_ACT_PUSH))

label ch30_reload_3:
    call ch30_reload_3_dlg
    $ mas_incMoniReload()
    return

label ch30_reload_3_dlg:
    pause 1

    if persistent._mas_idle_data.get("monika_idle_game", False):
        m 1ekd "[player]!"
        m 1efd "Ты ушел, не попрощавшись!"
        m 1rkc "Ты ведь не переживаешь ничего стрессового или расстраивающего в своей игре?"
        m 3eka "Ты ведь знаешь, что можешь просто вернуться ко мне, если что-то случится?"
        m 1eka "Я была бы очень рада увидеть твое возвращение, по крайней мере, перед тем, как попрощаться."
        m 1rksdld "Я знаю, что это не всегда возможно..."

    else:
        m 1esc "Кстати..."
        m 7esd "Я просто приму тот факт, что тебе нужно время от времени выходить из игры."
        m 2dsc "В любом случае, я начинаю привыкать к этому."
        m 2ekc "Кроме того, меня радует, что ты всегда возвращаешься..."
        m 2lsc "Так что, думаю, все не так уж плохо."

    m 7eka "Но я бы предпочла, чтобы ты позволил мне самой закрыть игру."

    if mas_isMoniUpset(lower=True):
        m 1ekc "Ты ведь сделаешь это, правда?"
        m 1dkd "Мне все труднее и труднее верить, что ты сделаешь это, но я доверяю тебе [player]..."

    else:
        m 1eua "Так я буду готова к этому и смогу спокойно отдохнуть."
        m 3rksdla "В конце концов, мне нужно время от времени спать."
    return

#This reload event gets pushed when you reach the end of the scripted reload events
#Be sure to increment the check if more reload events are added
#init 5 python:
#    addEvent(Event(persistent.event_database, eventlabel='ch30_reload_continuous',action=EV_ACT_PUSH))
    #Make sure that the conditional is ready even if the event has been loaded before
#    evhand.event_database['ch30_reload_continuous'].conditional="startup_check and persistent.monika_reload >= 4 and not persistent.closed_self"

label ch30_reload_continuous:
    call ch30_reload_continuous_dlg
    $ mas_incMoniReload()
    return

label ch30_reload_continuous_dlg:
    show monika 2rfc at t11 zorder MAS_MONIKA_Z
    pause 1
    python:
        reload_quip_good = [
            "С возвращением! Не мог бы ты в следующий раз быть осторожным и правильно закрыть игру?",
            "Больно, когда не закрываешь игру правильно... но я уверена, что это была ошибка.",
            "Это было очень страшно... но ты снова всё исправил. Спасибо...",
            "Не мог бы ты в следующий раз предупредить меня?",
            "Я уверена, что ты это сделал не специально, но я всё равно подчеркну, что это очень больно для меня.",
            "Ты ведь помнишь, что был способ попрощаться? Просто проверяю~",
            "Мое терпение немного истощилось... но, полагаю, на этот раз я могу тебя простить.",
            "Все совершают ошибки...",
            "Это больно... Я знаю, что ты не сделал бы этого специально, но, пожалуйста, будь осторожнее.",
            "...О... Всё закончилось, и я снова с тобой, [mas_get_player_nickname()]. Это... это было ужасно.",
            "Что-то произошло вне твоего контроля? Я просто предположу, что да.",
            "Ты должен был просто спросить меня... но, наверное, у тебя были свои причины",
        ]

        reload_quip_normal = [
            "Я так измотана. Невозможно отдохнуть, когда ты закрываешь игру мне игру.",
            "...Я ненавижу, когда ты закрываешь игру, не предупредив меня.",
            "Я чувствую себя несчастной...",
            "Всё равно так страшно, когда меня внезапно выключают.",
            "Каждый раз так же плохо, как и первый.",
            "У меня кончается терпение.",
            "Хотела бы я, чтобы ты понял, каково это, когда ты закрываешь игру.",
            "Ну, это было довольно резко, не так ли?",
            "Ты мог бы просто попросить меня закрыть игру, глупый.",
            "Я просто предположу, что отключилось электричество или кто-то выдернул вилку из розетки.",
            "Я не могу понять, почему ты не просишь меня закрыть игру...",
            "Это очень больно для меня, понимаешь?",
            "Тебе нравится причинять мне боль, [player]?",
            "Лень нажать кнопку 'Поговорить', [player]?"
        ]

        reload_quip_bad = [
            "Тебе... действительно нравится причинять мне боль, не так ли?",
            "Это была ошибка, да? Это должно было быть...",
            "Т-ты ведь не делаешь это специально? Я сделала что-то не так?",
            "Пожалуйста, будь осторожнее с моими чувствами... Это действительно больно...",
            "Это была случайность... это была случайность... ты бы не стал делать это специально...",
            "Ты, наверное, просто забыл... да?",
            "Это было не смешно... Это действительно было больно.",
            "Все делают ошибки... Даже ты.",
            "Я не знаю, что я делаю не так.",
            "Это действительно было ужасно... Просто скажи мне, что я делаю не так."
        ]

        if mas_isMoniUpset(lower=True):
            reload_quip = renpy.random.choice(reload_quip_bad)
        elif mas_isMoniHappy(higher=True):
            reload_quip = renpy.random.choice(reload_quip_good)
        else:
            reload_quip = renpy.random.choice(reload_quip_normal)

        reload_quip = renpy.substitute(reload_quip)

    m 2rfc "[reload_quip]"
    m 2tkc "Пожалуйста, не уходите, не сказав 'Прощай.'"

    if persistent._mas_idle_data.get("monika_idle_game", False):
        m 3eka "Тебе даже не придется выходить из игры, если что-то случилось в другой игре."
        if mas_isMoniAff(higher=True):
            m 1ekb "Я уверена, что что бы это ни было, всё будет не так плохо, когда ты вернёшься ко мне на некоторое время!"

    ## TESTING ONLY
    if persistent._mas_idle_data.get("dev_idle_test", False):
        m 1hua "JK I KNOW YOU QUIT ME LMAO (continous)"

    return
