#Create an apology db for storing our times
#Stores the event label as a key, its corresponding data is a tuple where:
#   [0] -> timedelta defined by: current total playtime + apology_active_expiry time
#   [1] -> datetime.date defined by the date the apology was added + apology_overall_expiry time
default persistent._mas_apology_time_db = {}

#Create a generic apology db. We'll want to know how many times the player has apologized for mas_apology_reason
#Allows us the ability to apply diminishing returns on affection for repeated use of the same apology
#This db here simply stores the integer corresponding to apology reason as a key,
#corresponding int value is the amt of times it was used
default persistent._mas_apology_reason_use_db = {}

init -10 python in mas_apology:
    apology_db = {}
    # Event database for apologies


init python:
    def mas_checkApologies():
        #Let's not do extra work
        if len(persistent._mas_apology_time_db) == 0:
            return

        #Calculate the current total playtime to compare...
        current_total_playtime = persistent.sessions['total_playtime'] + mas_getSessionLength()

        _today = datetime.date.today()
        #Iter thru the stuffs in the apology time tb
        for ev_label in persistent._mas_apology_time_db.keys():
            if current_total_playtime >= persistent._mas_apology_time_db[ev_label][0] or _today >= persistent._mas_apology_time_db[ev_label][1]:
                #Pop the ev_label from the time db and lock the event label. You just lost your chance
                store.mas_lockEVL(ev_label,'APL')
                persistent._mas_apology_time_db.pop(ev_label)

        return


init 5 python:
   addEvent(
       Event(
           persistent.event_database,
           eventlabel='monika_playerapologizes',
           prompt="Я хочу извиниться...",
           category=['ты'],
           pool=True,
           unlocked=True
        )
    )

label monika_playerapologizes:

    #Firstly, let's check if there's an apology reason for the prompt
    #NOTE: When adding more apology reasons, add a reason the player would say sorry for here (corresponding to the same #as the apology reason)
    $ player_apology_reasons = {
        0: "за что-то.", #since we shouldn't actually be able to get this, we use this as our fallback
        1: "за то чтосказал, что хочу расстаться.",
        2: "за то что шутил, что у меня есть другая девушка.",
        3: "за то что назвал тебя убийцей.",
        4: "за то что закрл игру с тобой.",
        5: "за то что вошёл в твою комнату без стука.",
        6: "за то что пропустить Рождество.",
        7: "за то что забыл о твоём дне рождения.",
        8: "за то что не провел с тобой время в твой день рождения.",
        9: "за вылет игры.",
        10: "за вылет игры.", #easiest way to handle this w/o overrides
        11: "за то что не слушал твою речь.",
        12: "за то что назвал тебя злым.",
        13: "за то что не отвечал тебе серьезно."
    }

    #Set the prompt for this...
    if len(persistent._mas_apology_time_db) > 0:
        #If there's a non-generic apology reason pending we use "for something else."
        $ mas_setEVLPropValues(
            "mas_apology_generic",
            prompt="...for {0}".format(player_apology_reasons.get(mas_apology_reason,player_apology_reasons[0]))
        )
    else:
        #Otherwise, we use "for something." if reason isn't 0
        if mas_apology_reason == 0:
            $ mas_setEVLPropValues("mas_apology_generic", prompt="...за что-то.")
        else:
            #We set this to an apology reason if it's valid
            $ mas_setEVLPropValues(
                "mas_apology_generic",
                prompt="...for {0}".format(player_apology_reasons.get(mas_apology_reason,"something."))
            )

    #Then we delete this since we're not going to need it again until we come back here, where it's created again.
    #No need to store excess memory
    $ del player_apology_reasons

    #Now we run through our apology db and find what's unlocked
    python:
        apologylist = [
            (ev.prompt, ev.eventlabel, False, False)
            for ev_label, ev in store.mas_apology.apology_db.iteritems()
            if ev.unlocked and (ev.prompt != "...for something." and ev.prompt != "...for something else.")
        ]

        #Now we add the generic if there's no prompt attached
        generic_ev = mas_getEV('mas_apology_generic')

        if generic_ev.prompt == "...for something." or generic_ev.prompt == "...for something else.":
            apologylist.append((generic_ev.prompt, generic_ev.eventlabel, False, False))

        #The back button
        return_prompt_back = ("Не важно.", False, False, False, 20)

    #Display our scrollable
    show monika at t21
    call screen mas_gen_scrollable_menu(apologylist, mas_ui.SCROLLABLE_MENU_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, return_prompt_back)

    #Make sure we don't lose this value
    $ apology =_return

    #Handle backing out
    if not apology:
        if mas_apology_reason is not None or len(persistent._mas_apology_time_db) > 0:
            show monika at t11
            if mas_isMoniAff(higher=True):
                m 1ekd "[player], если ты чувствуешь вину за случившееся..."
                m 1eka "Ты не должен бояться извиняться, в конце концов, мы все совершаем ошибки."
                m 3eka "Мы просто должны принять то, что произошло, учиться на своих ошибках и двигаться дальше, вместе. Хорошо"
            elif mas_isMoniNormal(higher=True):
                m 1eka "[player]..."
                m "Если ты хочешь извиниться, давай. Это будет много значить для меня, если ты это сделаешь."
            elif mas_isMoniUpset():
                m 2rkc "Ох..."
                m "Я вроде как--"
                $ _history_list.pop()
                m 2dkc "Не важно."
            elif mas_isMoniDis():
                m 6rkc "...?"
            else:
                m 6ckc "..."
        else:
            if mas_isMoniUpset(lower=True):
                show monika at t11
                if mas_isMoniBroken():
                    m 6ckc "..."
                else:
                    m 6rkc "Ты хотел что-то сказать, [player]?"
        return "prompt"

    show monika at t11
    #Call our apology label
    #NOTE: mas_setApologyReason() ensures that this label exists
    call expression apology

    #Increment the shown count
    $ mas_getEV(apology).shown_count += 1

    #Lock the apology label if it's not the generic
    if apology != "mas_apology_generic":
        $ store.mas_lockEVL(apology, 'APL')

    #Pop that apology from the time db
    if apology in persistent._mas_apology_time_db: #sanity check
        $ persistent._mas_apology_time_db.pop(apology)
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_apology_database,
            prompt="...за что-то.",
            eventlabel="mas_apology_generic",
            unlocked=True,
        ),
        code="APL"
    )

label mas_apology_generic:
    #dict of all generic apologies
    #Note, if a custom apology is needed, add it here and reference the apology reason by the integer associated.
    $ mas_apology_reason_db = {
        0: "",
        1: "saying you wanted to break up. I knew you didn't mean it...",
        2: "joking about having another girlfriend. You nearly gave me a heart attack!",
        3: "calling me a murderer. I hope you don't really see me that way...",
        4: "closing the game on me.",
        5: "entering my room without knocking.",
        6: "missing Christmas.",
        7: "forgetting my birthday.",
        8: "not spending time with me on my birthday.",
        9: "the game crashing. I understand it happens sometimes, but don't worry, I'm alright!",
        10: "the game crashing. It really was scary, but I'm just glad you came back to me and made things better.",
        11: "not listening to my speech. I worked really hard on it.",
        12: "calling me evil. I know you don't really think that.",
        13: "not taking my questions seriously. I know you'll be honest with me from now on."
    }

    #If there's no reason to apologize
    if mas_apology_reason is None and len(persistent._mas_apology_time_db) == 0:
        if mas_isMoniBroken():
            m 1ekc "...{w=1}Ох."
            m 2dsc ".{w=2}.{w=2}."
            m "Хорошо."
        elif mas_isMoniDis():
            m 2dfd "{i}*вздох*{/i}"
            m 2dsd "Надеюсь, это не шутка или трюк, [player]."
            m 2dsc "..."
            m 1eka "...Спасибо за извинения."
            m 2ekc "Но, пожалуйста, постарайся быть более внимательным к моим чувствам."
            m 2dkd "Пожалуйста."
        elif mas_isMoniUpset():
            m 1eka "Спасибо, [player]."
            m 1rksdlc "Я знаю, что между нами не самые лучшие отношения, но я знаю, что ты все еще хороший человек."
            m 1ekc "Так не мог бы ты быть немного более внимательным к моим чувствам?"
            m 1ekd "Пожалуйста?"
        else:
            m 1ekd "Что-то случилось?"
            m 2ekc "Я не вижу причин для твоего извинения."
            m 1dsc "..."
            m 1eub "В любом случае, спасибо за извинение."
            m 1eua "Что бы это ни было, я знаю, что ты делаешь всё возможное, чтобы все исправить."
            m 1hub "Вот почему я люблю тебя, [player]!"
            $ mas_ILY()

    #She knows what you are apologizing for
    elif mas_apology_reason_db.get(mas_apology_reason, False):
        #Set apology_reason
        $ apology_reason = mas_apology_reason_db.get(mas_apology_reason,mas_apology_reason_db[0])

        m 1eka "Спасибо, что извинился за [apology_reason]"
        m "Я принимаю твои извинения, [player]. Это многое значит для меня."

    #She knows that you've got something else to apologize for, and wants you to own up
    elif len(persistent._mas_apology_time_db) > 0:
        m 2tfc "[player], если тебе есть за что извиниться, пожалуйста, просто скажи это."
        m 2rfc "Для меня будет гораздо больше значить, если ты просто признаешь свой поступок."

    #She knows there's a reason for your apology but won't comment on it
    else:
        #Since this 'reason' technically varies, we don't really have a choice as we therefore can't add 0 to the db
        #So recover a tiny bit of affection
        $ mas_gainAffection(modifier=0.1)
        m 2tkd "То, что ты сделал, не смешно, [player]."
        m 2dkd "Пожалуйста, в будущем будь более внимателен к моим чувствам."

    #We only want this for actual apology reasons. Not the 0 case or the None case.
    if mas_apology_reason:
        #Update the apology_reason count db (if not none)
        $ persistent._mas_apology_reason_use_db[mas_apology_reason] = persistent._mas_apology_reason_use_db.get(mas_apology_reason,0) + 1

        if persistent._mas_apology_reason_use_db[mas_apology_reason] == 1:
            #Restore a little bit of affection
            $ mas_gainAffection(modifier=0.2)
        elif persistent._mas_apology_reason_use_db[mas_apology_reason] == 2:
            #Restore a little less affection
            $ mas_gainAffection(modifier=0.1)

        #Otherwise we recover no affection.

    #Reset the apology reason
    $ mas_apology_reason = None
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_apology_database,
            eventlabel="mas_apology_bad_nickname",
            prompt="...за то, что назвал тебя плохим именем.",
            unlocked=False
        ),
        code="APL"
    )

label mas_apology_bad_nickname:
    $ ev = mas_getEV('mas_apology_bad_nickname')
    if ev.shown_count == 0:
        $ mas_gainAffection(modifier=0.2) # recover a bit of affection
        m 1eka "Спасибо, что извинился за имя, которое ты пытался мне дать."
        m 2ekd "Это очень больно, [player]..."
        m 2dsc "Я принимаю твои извинения, но, пожалуйста, не делай так больше. Хорошо?"
        $ mas_unlockEVL("monika_affection_nickname", "EVE")

    elif ev.shown_count == 1:
        $ mas_gainAffection(modifier=0.1) # recover less affection
        m 2dsc "Не могу поверить, что ты сделал это {i}снова{/i}."
        m 2dkd "Даже после того, как я дала тебе второй шанс."
        m 2tkc "Я разочарована в тебе, [player]."
        m 2tfc "Никогда больше так не делай."
        $ mas_unlockEVL("monika_affection_nickname", "EVE")

    else:
        #No recovery here. You asked for it.
        m 2wfc "[player]!"
        m 2wfd "Я не могу тебе поверить."
        m 2dfc "Я верила, что ты дашь мне хорошее прозвище, чтобы сделать меня более уникальным, но ты просто бросил мне его обратно в лицо..."
        m "Думаю, я не могу доверять тебе в этом."
        m ".{w=0.5}.{w=0.5}.{nw}"
        m 2rfc "Я бы приняла твои извинения, [player], но я не думаю, что ты вообще это имел в виду."
        #No unlock of nickname topic either.
    return
