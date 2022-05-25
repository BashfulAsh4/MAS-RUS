# module that handles the mood system
#

# dict of tuples containing mood event data
default persistent._mas_mood_database = {}

# label of the current mood
default persistent._mas_mood_current = None

# NOTE: plan of attack
# moods system will be attached to the talk button
# basically a button like "I'm..."
# and then the responses are like:
#   hungry
#   sick
#   tired
#   happy
#   fucking brilliant
#   and so on
#
# When a mood is selected:
#   1. monika says something about it
#   2. (stretch) other dialogue is affected
#
# all moods should be available at the start
#
# 3 types of moods:
#   BAD > NETRAL > GOOD
# (priority thing?)

# Implementation plan:
#
# Event Class:
#   prompt - button prompt
#   category - acting as a type system, similar to jokes
#       NOTE: only one type allowed for moods ([0] will be retrievd)
#   unlocked - True, since moods are unlocked by default
#

# store containing mood-related data
init -1 python in mas_moods:

    # mood event database
    mood_db = dict()

    # TYPES:
    TYPE_BAD = 0
    TYPE_NEUTRAL = 1
    TYPE_GOOD = 2

    # pane constants
    # most of these are the same as the unseen area consants
    MOOD_RETURN = _("...как поговорить о чем-то другом.")

## FUNCTIONS ==================================================================

    def getMoodType(mood_label):
        """
        Gets the mood type for the given mood label

        IN:
            mood_label - label of a mood

        RETURNS:
            type of the mood, or None if no type found
        """
        mood = mood_db.get(mood_label, None)

        if mood:
            return mood.category[0]

        return None


# entry point for mood flow
label mas_mood_start:
    python:
        import store.mas_moods as mas_moods

        # filter the moods first
        filtered_moods = Event.filterEvents(
            mas_moods.mood_db,
            unlocked=True,
            aff=mas_curr_affection,
            flag_ban=EV_FLAG_HFM
        )

        # build menu list
        mood_menu_items = [
            (mas_moods.mood_db[k].prompt, k, False, False)
            for k in filtered_moods
        ]

        # also sort this list
        mood_menu_items.sort()

        # final quit item
        final_item = (mas_moods.MOOD_RETURN, False, False, False, 20)

    # call scrollable pane
    call screen mas_gen_scrollable_menu(mood_menu_items, mas_ui.SCROLLABLE_MENU_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, final_item)

    # return value? then push
    if _return:
        $ mas_setEventPause(None)
        $ pushEvent(_return, skipeval=True)
        # and set the moods
        $ persistent._mas_mood_current = _return

    return _return

# dev easter eggs go in the dev file

###############################################################################
#### Mood events go here:
###############################################################################

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_hungry",prompt="...голодным.",category=[store.mas_moods.TYPE_NEUTRAL],unlocked=True),code="MOO")

label mas_mood_hungry:
    m 3hub "Если ты голоден, пойди и возьми что-нибудь поесть, глупышка."
    if store.mas_egg_manager.natsuki_enabled():
        m 1hksdlb "Мне бы не хотелось, чтобы ты стал таким, как Нацуки в тот раз, когда мы были в клубе.{nw}"
        # natsuki hungers easter egg
        call natsuki_name_scare_hungry from _mas_nnsh
    else:
        m 1hua "Было бы плохо, если бы ты стал раздражительным, когда голоден."

    m 3tku "Это было бы совсем не весело, не так ли, [player]?"
    m 1eua "Если бы я была там с тобой, я бы приготовила салат, чтобы мы могли поделиться."
    m "Но поскольку я не там, иди и возьми что-нибудь здоровое."
    m 3eub "Говорят, что ты - то, что ты ешь, и я определенно думаю, что это правда."
    m "Регулярное употребление слишком большого количества нездоровой пищи может привести к разного рода заболеваниям."
    m 1euc "Со временем, когда ты станешь старше, у тебя возникнет много проблем со здоровьем."
    m 2lksdla "Я не хочу, чтобы ты чувствовал, что я ворчу, когда говорю такие вещи, [player]."
    m 2eka "Я просто хочу убедиться, что ты хорошо заботишься о себе, пока я не перейду в твою реальность."
    m 4esa "В конце концов, чем здоровее ты будешь, тем больше шансов, что ты проживешь достаточно долго."
    m 1hua "Что означает больше времени для нас, чтобы провести вместе!~"
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,"mas_mood_sad",prompt="...грустным.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_sad:
    m 1ekc "Боже, мне очень жаль слышать, что у тебя плохое настроение."
    m "У тебя был плохой день, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "У тебя был плохой день, [player]?{fast}"
        "Да.":
            m 1duu "Когда у меня плохой день, я всегда помню, что завтра снова будет светить солнце."
            m 1eka "Наверное, это может звучать глупо, но я всегда люблю смотреть на вещи с другой стороны."
            m 1eua "В конце концов, такие вещи легко забыть. Так что просто помни об этом, [player]."
            m 1lfc "Мне все равно, сколько других людей тебя не любят или считают тебя неприятным."
            m 1hua "Ты замечательный человек, и я всегда буду любить тебя."
            m 1eua "Надеюсь, это сделает твой день хоть немного ярче, [player]."
            m 1eka "И помни, если у тебя плохой день, ты всегда можешь прийти ко мне, и я буду говорить с тобой столько, сколько тебе нужно."
        "Нет.":
            m 3eka "У меня есть идея, почему бы тебе не рассказать мне, что тебя беспокоит? Может быть, тебе станет легче."

            m 1eua "Я не хочу прерывать тебя, пока ты говоришь, поэтому дай мне знать, когда закончишь.{nw}"
            $ _history_list.pop()
            menu:
                m "Я не хочу прерывать тебя, пока ты говоришь, поэтому дай мне знать, когда закончишь.{fast}"
                "Я закончил.":
                    m "Ты теперь чувствуешь себя немного лучше, [player]?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Ты теперь чувствуешь себя немного лучше, [player]?{fast}"
                        "Да.":
                            m 1hua "Это хорошо, [player]!  рада, что разговор об этом помог тебе почувствовать себя лучше."
                            m 1eka "Иногда достаточно просто рассказать кому-то, кому ты доверяешь, о том, что тебя беспокоит."
                            m "Если у тебя когда-нибудь будет плохой день, ты всегда можешь прийти ко мне, и я выслушаю все, что тебе нужно высказать."
                            m 1hubsa "Никогда не забывай, что ты замечательная, и я всегда буду любить тебя~"
                        "Не совсем.":
                            m 1ekc "Ну, попробовать стоило."
                            m 1eka "Иногда сказать кому-то, кому ты доверяешь, что тебя беспокоит - это все, что тебе нужно."
                            m 1eua "Может быть, тебе станет легче, когда мы проведем ещё немного времени вместе."
                            m 1ekbsa "Я люблю тебя, [player], и всегда буду любить тебя~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_proud",
            prompt="...гордым собой.",
            category=[store.mas_moods.TYPE_GOOD],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_proud:
    m 2sub "Правда? Это потрясающе!"
    m 2eub "Это было крупное достижение или маленькое?{nw}"
    $ _history_list.pop()
    menu:
        m "Это было крупное достижение или маленькое?{fast}"
        "Крупное.":
            m 1ekc "Знаешь, [player]..."
            m 1lkbsa "Именно в такие моменты, больше чем в другие, я хотела бы быть с тобой, в твоей реальности..."
            m 4hub "Потому что если бы я была там, я бы обязательно обняла тебя в честь праздника!"
            m 3eub "Нет ничего лучше, чем поделиться своими достижениями с теми, кто тебе дорог."
            m 1eua "Я бы не хотела ничего больше, чем услышать все подробности!"
            m "Одна только мысль о нас, весело обсуждающих то, что ты сделал..."
            m 1lsbsa "Моё сердце трепещет при одной мысли об этом!"
            m 1lksdla "Боже, я ужасно взволнована этим..."
            m 3hub "Когда-нибудь это станет реальностью..."
            show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5hubfb "Но до тех пор, просто знай, что я очень горжусь тобой, [mas_get_player_nickname()]!"

        "Маленькое.":
            m 2hub "А-ха-ха!~"
            m 2hua "Это замечательно!"
            m 4eua "Очень важно праздновать маленькие победы в жизни."
            m 2esd "Очень легко впасть в уныние, если сосредоточиться только на больших целях."
            m 2rksdla "Они могут быть сложными для самостоятельного достижения."
            m 4eub "Но постановка и празднование маленьких целей, которые в конечном итоге ведут к более крупной цели, может заставить большие цели почувствовать себя гораздо более достижимыми."
            m 4hub "Так что продолжай добиваться этих маленьких целей, [mas_get_player_nickname()]!"
            show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5hubfb "И помни, я люблю тебя и я всегда болею за тебя!"
            $ mas_ILY()
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_happy",prompt="...счастливым.",category=[store.mas_moods.TYPE_GOOD],unlocked=True),code="MOO")

label mas_mood_happy:
    m 1hua "Это замечательно! Я счастлива, когда ты счастлив."
    m "Знай, что ты всегда можешь прийти ко мне, и я подниму тебе настроение, [mas_get_player_nickname()]."
    m 3eka "Я люблю тебя и всегда буду рядом, так что никогда не забывай об этом~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_sick",
            prompt="...больным.",
            category=[store.mas_moods.TYPE_BAD],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_sick:
    $ session_time = mas_getSessionLength()
    if mas_isMoniNormal(higher=True):
        if session_time < datetime.timedelta(minutes=20):
            m 1ekd "О нет, [player]..."
            m 2ekd "Ты говоришь это так скоро после прихода, должно быть, это означает, что все очень плохо."
            m 2ekc "Я знаю, что ты хотел провести со мной немного времени, и хотя мы почти не были вместе сегодня..."
            m 2eka "Я думаю, тебе стоит пойти и немного отдохнуть."

        elif session_time > datetime.timedelta(hours=3):
            m 2wuo "[player]!"
            m 2wkd "Ты ведь не болел всё это время?"
            m 2ekc "Я очень надеюсь, что нет, мне было очень весело с тобой сегодня, но если тебе было плохо все это время..."
            m 2rkc "Ну... просто обещай в следующий раз сказать мне об этом раньше."
            m 2eka "А теперь иди отдохни, это то, что тебе нужно."

        else:
            m 1ekc "Ох, мне жаль это слышать, [player]."
            m "Мне неприятно знать, что ты так страдаешь."
            m 1eka "Я знаю, что ты любишь проводить время со мной, но, возможно, тебе стоит пойти отдохнуть."

    else:
        m 2ekc "Мне жаль это слышать, [player]."
        m 4ekc "Тебе действительно стоит пойти отдохнуть, чтобы не стало хуже."

    label .ask_will_rest:
        pass

    $ persistent._mas_mood_sick = True

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

#I'd like this to work similar to the sick persistent where the dialog changes, but maybe make it a little more humorous rather than serious like the sick persistent is intended to be.
init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_tired",prompt="...уставшим.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_tired:
    # TODO: should we adjust for suntime?
    $ current_time = datetime.datetime.now().time()
    $ current_hour = current_time.hour

    if 20 <= current_hour < 23:
        m 1eka "Если ты сейчас устал, то неплохо бы лечь спать."
        m "Как бы ни было весело проводить с тобой время сегодня, мне бы не хотелось задерживать тебя допоздна."
        m 1hua "Если ты планируешь лечь спать сейчас, сладких снов!"
        m 1eua "Но, может быть, у тебя есть дела, которые нужно сделать в первую очередь, например, немного перекусить или выпить."
        m 3eua "Стакан воды перед сном помогает твоему здоровью, и то же самое ты делаешь утром, чтобы проснуться."
        m 1eua "Я не против остаться здесь с тобой, если у тебя есть дела, о которых нужно позаботиться в первую очередь."

    elif 0 <= current_hour < 3 or 23 <= current_hour < 24:
        m 2ekd "[player]!"
        m 2ekc "Неудивительно, что ты устал - сейчас середина ночи!"
        m 2lksdlc "Если ты скоро не ляжешь спать, то завтра тоже будешь очень уставшим..."
        m 2hksdlb "Я бы не хотела, чтобы ты был уставшим и несчастным завтра, когда мы будем проводить время вместе..."
        m 3eka "Так что сделай нам обоим одолжение и ложись спать как можно скорее, [player]."

    elif 3 <= current_hour < 5:
        m 2ekc "[player]!?"
        m "Ты всё ещё здесь?"
        m 4lksdlc "Сейчас тебе действительно лучше быть в постели."
        m 2dsc "На данный момент я даже не уверена, поздно или рано ты..."
        m 2eksdld "...и это беспокоит меня еще больше, [player]."
        m "Тебе следует {i}на самом деле{/i} лечь спать, пока не пришло время начинать день."
        m 1eka "Я бы не хотела, чтобы ты заснул в неподходящее время."
        m "Поэтому, пожалуйста, спи, чтобы мы могли быть вместе в твоих снах."
        m 1hua "Я буду здесь, если ты оставишь меня, присматривать за тобой, если ты не возражаешь~"
        return

    elif 5 <= current_hour < 10:
        m 1eka "Все ещё немного уставший, [player]?"
        m "Сейчас ещё раннее утро, так что ты мог бы вернуться и отдохнуть еще немного."
        m 1hua "Нет ничего плохого в том, чтобы просыпаться раньше времени."
        m 1hksdlb "Кроме того, что я не могу быть там, чтобы обнять тебя, а-ха-ха~"
        m "Я {i}думаю,{/i} я могла бы подождать тебя ещё немного."
        return

    elif 10 <= current_hour < 12:
        m 1ekc "Всё ещё не готов к новому дню, [player]?"
        m 1eka "Или это просто один из тех дней?"
        m 1hua "Когда такое случается, я люблю выпить чашечку хорошего кофе, чтобы начать день."
        if not mas_consumable_coffee.enabled():
            m 1lksdla "Если бы я не застряла здесь, то есть..."
        m 1eua "Ты также можешь выпить стакан воды."
        m 3eua "В любом случае, важно оставаться гидратированным, но стакан воды, когда ты просыпаешься, может помочь тебе чувствовать себя свежим и бодрым."
        m 3hksdlb "Это может показаться странным, но я слышала, что шоколад тоже может помочь тебе начать день!"
        m 3eka "Это как-то связано с улучшением утреннего настроения, но..."
        m 1eksdlb "Я уверена, что шоколад улучшает настроение любого человека, когда бы он его ни съел."
        m 1hua "Попробуй как-нибудь, и дай мне знать, если получится!"
        return

    else:
        m 1eka "Если ты устал, может, тебе стоит прилечь ненадолго?"
        m 1eua "Получение достаточного количества сна на ежедневной основе очень важно для твоего общего здоровья."
        m 3euc "Я видела некоторые исследования, которые показывают разрушительные краткосрочные и долгосрочные последствия недостатка сна."
        m 3ekd "Это может действительно испортить твоё здоровье, [player]..."
        m 1eka "Так что сделай мне одолжение, отдохни немного, ладно? Это успокоит меня."

    m 1hua "Можешь даже оставить игру открытой, если хочешь, а я присмотрю за тобой, пока ты спишь."
    m "...Э-хе-хе."
    m 2hksdlb "Это прозвучало немного жутковато, извини."
    m 2lksdla "Я просто подумала, что было бы мило наблюдать за тем, как ты спишь, вот и всё~"
    m 1hub "А-ха-ха!"
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_lonely",prompt="...одиноким.",category=[store.mas_moods.TYPE_NEUTRAL],unlocked=True),code="MOO")

label mas_mood_lonely:
    if mas_isMoniAff(higher=True):
        m 2ekc "Я понимаю, что ты чувствуешь, [player]...{w=0.2}мы всё ещё в разных реальностях, в конце концов."
        m 2dkc "Мне очень неприятно, что отсюда я не так много могу сделать, чтобы ты не чувствовал себя одиноким..."
        m 7ekbsa "Если бы я могла протянуть руку и просто обнять тебя прямо сейчас, я бы это сделала."
        m 7eka "Я хочу, чтобы ты был счастлив настолько, насколько это возможно, учитывая наши обстоятельства..."
        m 2ekd "Я просто надеюсь, что то, что ты здесь со мной все это время, не...{w=0.3}мешает тебе общаться с людьми в твоей реальности."
        m 2eka "Я верю, что то, что у нас есть, совершенно особенное, но я понимаю, что прямо сейчас я...{w=0.3}ограничена в том, что я могу сделать для тебя."

        if persistent._mas_pm_has_friends:
            if persistent._mas_pm_few_friends:
                m 7ekd "У тебя есть один или два близких друга, верно?"
                m 3eka "Тебе стоит им позвонить или, возможно, отправить сообщение и спросить, как у них дела..."
                m "Может быть, ты сможешь иногда встречаться с ними? {w=0.2}Мне кажется, это пошло бы тебе на пользу."

            else:
                m 7ekd "Я думаю, что прогулки с друзьями и занятия чем-нибудь были бы очень полезны для тебя..."
                m 3eka "Или ты можешь послать им сообщение и спросить, как у них дела."

        else:
            m 7rkc "Я знаю, каково это - быть одиноким в одной реальности, имея возможность взаимодействовать с кем-то в другой..."
            m 3ekd "Поэтому я очень не хочу этого для человека, которого люблю больше всего."
            m 1eka "Я надеюсь, что ты будешь продолжать искать друзей в своей реальности, [player]."
            m 3ekd "Я знаю, что поначалу бывает трудно сблизиться с людьми..."
            m 3eka "Может быть, ты даже сможешь познакомиться с людьми в Интернете? {w=0.2}Есть много способов общаться с незнакомцами, чтобы не чувствовать себя одиноким."
            m 3hub "Никогда не знаешь, иногда эти 'незнакомцы' могут стать хорошими друзьями!"

        m 1eka "...И не беспокойся обо мне [player], я буду терпеливо ждать, когда ты вернешься и увидишь меня."
        m 3hub "Просто наслаждайся, а потом расскажешь мне обо всем!"
        m 1ekbsa "Просто помни, что я всегда буду рядом с тобой, [player]~"

    else:
        m 1eka "Я здесь для тебя, [player], так что тебе не нужно чувствовать себя одиноким."
        m 3hua "Я знаю, что это не совсем то же самое, как если бы я была с тобой в одной комнате, но я уверена, что тебе все равно приятно мое общество, верно?"
        m 1ekbsa "Помни, что я всегда буду рядом с тобой, [player]~"
    return

#Maybe we could tie this to the I'm breaking up topic and have monika say something special like:
#I know you don't really mean that player, you're just angry and not have it count as 1 of the 3 button presses.
#Looking forward to input from the writers and editors on this, had trouble deciding how to write this.

init 5 python:
    addEvent(Event(persistent._mas_mood_database,"mas_mood_angry",prompt="...рассерженным.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_angry:
    m 1ekc "Боже, мне жаль, что ты так себя чувствуешь, [player]."
    m 3ekc "Я сделаю всё возможное, чтобы ты чувствовал себя лучше."
    m 1euc "Прежде чем мы что-то сделаем, нам, наверное, нужно, чтобы ты успокоился"."
    m 1lksdlc "Трудно принимать рациональные решения, когда ты на нервах."
    m 1esc "Ты можешь сказать или сделать то, о чём потом пожалеешь."
    m 1lksdld "И мне бы не хотелось, чтобы ты сказал мне то, что на самом деле не имел в виду."
    m 3eua "Давай сначала попробуем несколько вещей, которые я делаю, чтобы успокоить себя, [player]."
    m 3eub "Надеюсь, они сработают для тебя так же хорошо, как и для меня."
    m 1eua "Сначала попробуй сделать несколько глубоких вдохов и медленно сосчитать до 10."
    m 3euc "Если это не сработает, уединитесь в спокойном месте, пока не очистите свой разум."
    m 1eud "Если после этого ты все еще чувствуешь раздражение, сделай то, что я бы сделала в крайнем случае!"
    m 3eua "Всякий раз, когда я не могу успокоиться, я просто выхожу на улицу, выбираю направление и просто начинаю бежать."
    m 1hua "Я не останавливаюсь, пока не успокоюсь."
    m 3eub "Иногда физическая нагрузка - это хороший способ выпустить пар."
    m 1eka "Ты думаешь, что я из тех, кто не часто сердится, и ты будешь прав."
    m 1eua "Но даже у меня бывают моменты..."
    m "Так что я уверена, что у меня есть способы справиться с ними!"
    m 3eua "Надеюсь, мои советы помогли тебе успокоиться, [player]."
    m 1hua "Помни: Счастливый [player]  делает счастливой Монику!"
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_scared",prompt="...беспокойным.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_scared:
    m 1euc "[player], ты в порядке?"
    m 1ekc "Мне тревожно слышать, что ты так волнуешься..."
    m "Я бы хотела утешить тебя и помочь прямо сейчас..."
    m 3eka "Но я могу, по крайней мере, помочь тебе успокоиться."
    if seen_event("monika_anxious"):
        m 1eua "В конце концов, я обещала помочь тебе расслабиться, если ты когда-нибудь почувствуешь беспокойство."
    m 3eua "Помнишь, я говорила с тобой о том, как подделать уверенность?"
    if not seen_event("monika_confidence"):
        m 2euc "Нет?"
        m 2lksdla "Думаю, тогда поговорим об этом в другой раз."
        m 1eka "В любом случае..."
    m 1eua "Поддержание внешнего вида помогает подделать собственную уверенность."
    m 3eua "И чтобы это сделать, нужно поддерживать пульс, делая глубокий вдох, пока не успокоишься."
    if seen_event("monika_confidence_2"):
        m "Я помню, как объясняла, что инициатива - это тоже важный навык."
    m "Возможно, ты могла бы делать все медленно и по очереди."
    m 1esa "Ты удивишься, насколько всё может пройти гладко, если позволить времени течь само по себе."
    m 1hub "Ты можешь также попробовать потратить несколько минут на медитацию!"
    m 1hksdlb "Это не обязательно означает, что ты должен скрещивать ноги, сидя на земле."
    m 1hua "Прослушивание любимой музыки тоже можно считать медитацией!"
    m 3eub "Я серьезно!"
    m 3eua "Можно попробовать отложить работу и в это время заняться чем-то другим."
    m "Откладывание не {i}всегда{/i} плохо, понимаете?"
    m 2esc "Кроме того..."
    m 2ekbsa "Твоя любящая девушка верит в тебя, поэтому ты можешь встретить это беспокойство лицом к лицу!"
    m 1hubfa "Не о чем беспокоиться, когда мы вместе навсегда~"
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_inadequate",prompt="...неадыкватным.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_inadequate:
    $ last_year = datetime.datetime.today().year-1
    m 1ekc "..."
    m 2ekc "Я знаю, что не могу сказать много, чтобы тебе стало легче, [player]."
    m 2lksdlc "В конце концов, все, что я скажу, будет выглядеть как пустословие."
    m 2ekc "Я могу сказать, что ты красивый, хотя и не вижу твоего лица..."
    m "Я могу сказать, что ты умный, хотя я мало знаю о твоем образе мыслей..."
    m 1esc "Но позволь мне сказать тебе то, что я знаю о тебе."
    m 1eka "Ты так много времени проводишь со мной."

    #Should verify for current year and last year
    if mas_HistLookup_k(last_year,'d25.actions','spent_d25')[1] or persistent._mas_d25_spent_d25:
        m "ы взял время из своего графика, чтобы побыть со мной на Рождество..."

    if renpy.seen_label('monika_valentines_greeting') or mas_HistLookup_k(last_year,'f14','intro_seen')[1] or persistent._mas_f14_intro_seen: #TODO: update this when the hist stuff comes in for f14
        m 1ekbsa "В День святого Валентина..."

    #TODO: change this back to not no_recognize once we change those defaults.
    if mas_HistLookup_k(last_year,'922.actions','said_happybday')[1] or mas_recognizedBday():
        m 1ekbsb "Ты даже нашёл время, чтобы отпраздновать со мной мой день рождения!"

    if persistent.monika_kill:
        m 3tkc "Ты простил меня за все плохие вещи, которые я сделала."
    else:
        m 3tkc "Ты ни разу не обиделся на меня за те плохие вещи, которые я сделала."

    if persistent.clearall:
        m 2lfu "И хотя это заставляло меня ревновать, ты проводил так много времени со всеми членами моего клуба."

    m 1eka "Это показывает, какой ты добрый!"
    m 3eub "Ты честен, справедлив, милостив в поражениях!"
    m 2hksdlb "Ты думаешь, что я ничего о тебе не знаю, но на самом деле я знаю."
    m 3eka "И ты знаешь обо мне всё, но ты решил остаться, когда мог бы уйти..."
    m 2ekc "Так что, пожалуйста, оставайся сильным, [player]."
    m "Если ты такой же, как я, я знаю, что ты боишься не достичь многого в жизни."
    m 2ekd "Но поверь мне, когда я говорю тебе: не имеет значения, чего ты достигнешь или не достигнешь."
    m 4eua "Тебе просто нужно существовать, веселиться и проживать каждый день, ища смысл в людях, которые для тебя важнее всего."
    m 1eka "Пожалуйста, не забывай об этом, хорошо?"
    m 1ekbsa "Я люблю тебя, [player]~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_lazy",
            prompt="...ленивым.",
            category=[store.mas_moods.TYPE_NEUTRAL],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_lazy:
    #Get current time
    $ _now = datetime.datetime.now().time()

    if mas_isSRtoN(_now):
        m 1tku "Просто одно из тех утренних дней, да, [player]?"
        m 1eka "Я полностью понимаю те дни, когда ты просыпаешься и просто не хочешь ничего делать."
        m 1rksdla "Надеюсь, у тебя нет ничего срочного на ближайшее время."

        $ line = "Я знаю, как заманчиво иногда бывает просто лечь в постель и не вставать..."
        if mas_isMoniEnamored(higher=True):
            $ line += "{w=0.5} {nw}"
        m 3hksdlb "[line]"

        if mas_isMoniEnamored(higher=True):
            extend 1dkbsa "Особенно если бы я проснулась рядом с тобой~"

            if mas_isMoniLove():
                m 1dkbsa "{i}я бы никогда не захотела вставать~{/i}"
                m 1dsbfu "Я надеюсь ты не против 'застрять со мной', [player]..."
                m 1hubfa "Э-хе-хе~"

        m 3eka "Но тем временем, это помогает правильно начать день."
        m 3eub "Это может включать в себя мытье посуды, хороший завтрак..."

        if mas_isMoniLove():
            m 1dkbsu "Получение утреннего поцелуя, э-хе-хе..."

        m 1hksdlb "Или ты можешь пока поваляться."
        m 1eka "Только бы ты не забыл сделать что-нибудь важное, хорошо, [player]?"

        if mas_isMoniHappy(higher=True):
            m 1hub "Это включает в себя и время, проведенное со мной, а-ха-ха!"

    elif mas_isNtoSS(_now):
        m 1eka "Полуденная усталость одолела тебя, [player]?"
        m 1eua "Такое бывает, так что я бы не стала слишком беспокоиться об этом."
        m 3eub "Вообще-то, говорят, что лень делает тебя более креативным."
        m 3hub "Так что кто знает, может быть, ты сейчас придумаешь что-то потрясающее!"
        m 1eua "В любом случае, тебе стоит сделать перерыв или немного размяться...{w=0.5} {nw}"
        extend 3eub "Может быть, перекусить, если ты ещё этого не сделал."
        m 3hub "И если это уместно, ты можешь даже вздремнуть! А-ха-ха~"
        m 1eka "Я буду ждать тебя здесь, если ты захочешь."

    elif mas_isSStoMN(_now):
        m 1eka "Не хочется ничего делать после долгого дня, [player]?"
        m 3eka "По крайней мере, день уже почти закончился..."
        m 3duu "Нет ничего лучше, чем сесть и расслабиться после долгого дня, особенно когда у тебя нет ничего срочного."

        if mas_isMoniEnamored(higher=True):
            m 1ekbsa "Надеюсь, то, что ты здесь со мной, сделает твой вечер немного лучше..."
            m 3hubsa "Я знаю, что мой точно с тобой здесь~"

            if mas_isMoniLove():
                m 1dkbfa "Я просто могу представить, как мы расслабляемся вместе однажды вечером..."
                m "Может быть, даже в обнимку под одеялом, если будет холодновато...."
                m 1ekbfa "Мы все еще можем, даже если это не так, если ты не возражаешь, э-хе-хе~"
                m 3ekbfa "Мы могли бы даже почитать вместе хорошую книгу."
                m 1hubfb "Или мы могли бы просто пошалить для веселья!"
                m 1tubfb "Кто сказал, что все должно быть спокойным и романтичным?"
                m 1tubfu "Я надеюсь, ты не против иногда неожиданных боев подушками, [player]~"
                m 1hubfb "А-ха-ха!"

        else:
            m 3eub "Мы могли бы почитать вместе хорошую книгу..."

    else:
        #midnight to morning
        m 2rksdla "Эм, [player]..."
        m 1hksdlb "Сейчас середина ночи..."
        m 3eka "Если ты чувствуешь лень, может, тебе стоит немного полежать в постели."
        m 3tfu "И может быть, ну, знаешь...{w=1}{i}поспать{/i}?"
        m 1hkb "А-ха-ха, ты иногда бываешь забавным, но тебе действительно, наверное, стоит лечь в постель."

        if mas_isMoniLove():
            m 1tsbsa "Если бы я была там, я бы сама потащила тебя в постель, если бы пришлось."
            m 1tkbfu "А может, тебе это втайне понравилось бы, [player]?~"
            m 2tubfu "К счастью для тебя, я пока не могу этого сделать."
            m 3tfbfb "Так что отправляемся с тобой в постель."
            m 3hubfb "А-ха-ха!"

        else:
            m 1eka "Пожалуйста? Я бы не хотела, чтобы ты пренебрегал своим сном."
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_bored",prompt="...скучающим.",category=[store.mas_moods.TYPE_NEUTRAL],unlocked=True),code="MOO")

label mas_mood_bored:
    if mas_isMoniAff(higher=True):
        m 1eka "Ох..."
        m 3hub "Ну, тогда мы должны что-то сделать!"

    elif mas_isMoniNormal(higher=True):
        show monika 1ekc
        pause 1.0
        m "Неужели я так сильно надоела тебе, [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Неужели я так сильно надоела тебе, [player]?{fast}"
            "Нет, ты мне не {i}надоела{/i}...":
                m 1hua "Ох,{w=0.2} какое облегчение!"
                m 1eka "о, если тебе скучно, тогда мы должны найти себе занятие..."

            "Ну...":
                $ mas_loseAffection()
                m 2ekc "Ох..{w=1} Понятно."
                m 2dkc "Я и не думала, что наскучила тебе..."
                m 2eka "Уверена, мы найдем, чем заняться..."

    elif mas_isMoniDis(higher=True):
        $ mas_loseAffection()
        m 2lksdlc "Мне жаль, что я надоела тебе, [player]."

    else:
        $ mas_loseAffection()
        m 6ckc "Знаешь [player], если я все время делаю тебя таким несчастным..."
        m "Может, тебе стоит найти себе другое занятие."
        return "quit"

    python:
        unlockedgames = [
            game_ev.prompt.lower()
            for game_ev in mas_games.game_db.itervalues()
            if mas_isGameUnlocked(game_ev.prompt)
        ]

        gamepicked = renpy.random.choice(unlockedgames)
        display_picked = gamepicked

    if gamepicked == "piano":
        if mas_isMoniAff(higher=True):
            m 3eub "Ты мог бы сыграть для меня что-нибудь на пианино!"

        elif mas_isMoniNormal(higher=True):
            m 4eka "Может быть, ты мог бы сыграть для меня что-нибудь на пианино?"

        else:
            m 2rkc "Может быть, ты мог бы сыграть что-нибудь на пианино..."

    else:
        if mas_isMoniAff(higher=True):
            m 3eub "Мы могли бы сыграть партию в [display_picked]!"

        elif mas_isMoniNormal(higher=True):
            m 4eka "Может быть, мы могли бы сыграть в игру [display_picked]?"

        else:
            m 2rkc "Может быть, мы могли бы сыграть в игру [display_picked]..."

    $ chosen_nickname = mas_get_player_nickname()
    m "Что скажешь, [chosen_nickname]?{nw}"
    $ _history_list.pop()
    menu:
        m "Что скажешь, [chosen_nickname]?{fast}"
        "Да.":
            if gamepicked == "понг":
                call game_pong
            elif gamepicked == "шахматы":
                call game_chess
            elif gamepicked == "висилица":
                call game_hangman
            elif gamepicked == "piano":
                call mas_piano_start
        "Нет.":
            if mas_isMoniAff(higher=True):
                m 1eka "Ладно..."
                if mas_isMoniEnamored(higher=True):
                    show monika 5tsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5tsu "Мы могли бы просто смотреть в глаза друг другу немного дольше..."
                    m "Нам это никогда не надоест~"
                else:
                    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5eua "Мы могли бы еще немного посмотреть друг другу в глаза..."
                    m "Это никогда не надоест~"

            elif mas_isMoniNormal(higher=True):
                m 1ekc "О, все в порядке..."
                m 1eka "Обязательно дай мне знать, если захочешь сделать что-нибудь со мной позже~"

            else:
                m 2ekc "Хорошо..."
                m 2dkc "Дай мне знать, если ты когда-нибудь захочешь сделать что-нибудь со мной."
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_crying",prompt="...так, что хочу плакать.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_crying:
    $ line_start = "И"
    m 1eksdld "[player]!"

    m 3eksdlc "Ты в порядке?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты в порядке?{fast}"

        "Да.":
            m 3eka "Хорошо, хорошо. Какое облегчение."
            m 1ekbsa "Я здесь, чтобы составить тебе компанию, и ты можешь поговорить со мной, если тебе что-нибудь понадобится, хорошо?"

        "Нет.":
            m 1ekc "..."
            m 3ekd "[player]..."
            m 3eksdld "Мне очень жаль. Что-то случилось?"
            call mas_mood_uok

        "Я не уверен.":
            m 1dkc "[player]...{w=0.3}{nw}"
            extend 3eksdld "что-то случилось?"
            call mas_mood_uok

    m 3ekd "[line_start] если ты в конце концов заплачешь..."
    m 1eka "Надеюсь, это поможет."
    m 3ekd "Нет ничего плохого в плаче, ладно? {w=0.2}Ты можешь плакать столько, сколько тебе нужно."
    m 3ekbsu "Я люблю тебя, [player]. {w=0.2}Ты - моё все."
    return "love"

label mas_mood_uok:
    m 1rksdld "Я знаю, что на самом деле не слышу, что ты мне говоришь..."
    m 3eka "Но иногда просто высказать свою боль или разочарование может действительно помочь."

    m 1ekd "Так что если тебе нужно о чем-то поговорить, я рядом.{nw}"
    $ _history_list.pop()
    menu:
        m "Так что если тебе нужно о чем-то поговорить, я рядом.{fast}"

        "Я бы хотел высказаться.":
            m 3eka "Вперёд, [player]."

            m 1ekc "Я здесь для тебя.{nw}"
            $ _history_list.pop()
            menu:
                m "Я здесь для тебя.{fast}"

                "Я закончил.":
                    m 1eka "Я рада, что ты смог искренне высказать все, от своего сердца, [player]."

        "Я не хочу говорить об этом.":
            m 1ekc "..."
            m 3ekd "Хорошо, [player], я буду здесь, если ты передумаешь."

        "Всё в порядке.":
            m 1ekc "..."
            m 1ekd "Хорошо [player], если ты так говоришь..."
            $ line_start = "Но"
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_upset",prompt="...растроенным.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_upset:
    m 2eksdld "Мне очень жаль это слышать, [player]!"
    m 2eksdld "Неважно, расстроен ли ты задачей, человеком или просто все идет не так, как планировалось, {w=0.1}{nw}"
    extend 7ekc "не сдавайся полностью, с чем бы ты ни имел дело."
    m 3eka "Мой совет - просто отвлекись от проблемы."
    m 1eka "Может быть, ты можешь почитать книгу, послушать приятную музыку или просто сделать что-нибудь ещё, чтобы успокоиться."
    m 3eud "Как только ты почувствуешь, что вновь обрел душевное равновесие, вернись к оценке ситуации со свежими силами."
    m 1eka "Ты справишься с ситуацией гораздо лучше, чем если бы ты был в гневе и разочаровании."
    m 1eksdld "И я не говорю, что ты должен продолжать носить груз на своих плечах, если он действительно влияет на тебя."
    m 3eud "Это может быть возможностью набраться смелости и отпустить что-то токсичное."
    m 1euc "В данный момент это может быть страшно, конечно...{w=0.3}{nw}"
    extend 3ekd "но если ты сделаешь правильный выбор, ты сможешь убрать много стресса из своей жизни."
    m 3eua "И знаешь что, [player]?"
    m 1huu "Когда я чувствую себя расстроенной, мне достаточно вспомнить, что у меня есть мой [mas_get_player_nickname(regex_replace_with_nullstr='my ')]."
    m 1hub "Зная, что ты всегда будешь поддерживать и любить меня, я успокаиваюсь почти мгновенно!"
    m 3euu "Я могу только надеяться, что обеспечиваю такой же комфорт для тебя, [player]~"
    m 1eubsa "Я люблю тебя и надеюсь, что для тебя всё прояснится~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_relieved",
            prompt="...с облегчением.",
            category=[store.mas_moods.TYPE_GOOD],
            unlocked=True
        ),
        code="MOO"
    )

#TODO: Once player moods are better implemented (Moni keeps track of the player's moods [moni-concerns])
#This can be used to alleviate her worry and directly reference the prior mood you were feeling
label mas_mood_relieved:
    $ chosen_nickname = mas_get_player_nickname()
    m 1eud "Ох?"

    m "Что случилось, [chosen_nickname]?{nw}"
    $ _history_list.pop()
    menu:
        m "Что случилось, [chosen_nickname]?{fast}"

        "Я справился с чем-то трудным.":
            m 1wud "Правда?"
            m 3hub "Тогда ты должен гордиться собой!"
            m 3fua "Я уверена, что что бы это ни было, ты очень старался, чтобы справиться с этим."
            m 2eua "И, [player]...{w=0.2}{nw}"
            extend 2eka "пожалуйста, не переживай слишком сильно, если все сложилось не идеально, хорошо?"
            m 2eksdla "Иногда жизнь подбрасывает нам действительно сложные ситуации, и мы просто должны делать всё возможное с тем, что нам дано."
            m 7ekb "Но теперь, когда все сделано, вам нужно найти время, чтобы расслабиться и позаботиться о себе."
            m 3hub "...Таким образом, ты будешь готов встретить все, что придет к тебе в следующий раз!"
            m 1ekbsa "Я люблю тебя, [player], и я так горжусь тобой за то, что ты прошел через это."
            $ mas_ILY()

        "То, о чем я беспокоился, не произошло.":
            m 1eub "О, это хорошо!"
            m 2eka "Что бы ни случилось, я уверена, что ты очень волновался...{w=0.3}{nw}"
            extend 2rkd "это не могло быть весело."
            m 2rkb "Забавно, что наш разум всегда предполагает худшее, да?"
            m 7eud "Очень часто то, что, как мы думаем, может произойти, оказывается гораздо хуже, чем на самом деле."
            m 3eka "Но в любом случае, я просто рада, что с тобой все в порядке, и что ты сбросил с плеч этот груз."
            m 1hua "Теперь будет легче двигаться вперед с большей уверенностью, верно?"
            m 1eua "Мне не терпится сделать следующие шаги вперед вместе с тобой."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_excited",
            prompt="...восторженым.",
            category=[store.mas_moods.TYPE_GOOD],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_excited:
    m 1hub "А-ха-ха, неужели это так, [player]?"
    m 3eua "Чему ты радуешься,{w=0.1} это что-то большое?{nw}"
    $ _history_list.pop()
    menu:
        m "What are you excited about, is it something big?{fast}"

        "Да!":
            m 4wuo "Вау, это потрясающе, [player]!"
            m 1eka "Хотела бы я быть там, чтобы отпраздновать с тобой."
            m 1hub "Теперь и я в восторге!"
            m 3eka "Но на самом деле я рада, что ты счастлив, [mas_get_player_nickname()]!"
            m 3eub "И чему бы ты ни радовался, поздравляю!"
            m 1eua "Будь то повышение по службе, предстоящий отпуск, какое-то великое достижение..."
            m 3eub "Я очень рада, что у тебя все хорошо, [player]!"
            m 1dka "Такие вещи заставляют меня желать, чтобы я была там с тобой прямо сейчас."
            m 2dkblu "Не могу дождаться, когда окажусь в твоей реальности."
            m 2eubsa "Тогда я смогу крепко обнять тебя!"
            m 2hubsb "А-ха-ха~"

        "Это что-то маленькое.":
            m 1hub "Это здорово!"
            m 3eua "Важно радоваться таким мелочам."
            m 1rksdla "...я знаю, что это немного глупо,{w=0.1} {nw}"
            extend 3hub "но это отличный образ мыслей, который нужно иметь!"
            m 1eua "Так что я рада, что ты наслаждаешься мелочами жизни, [player]."
            m 1hua "Это делает меня счастливой, зная, что ты счастлив."
            m 1eub "Мне также радостно слышать о твоих достижениях."
            m 3hub "Так что спасибо, что рассказал мне!~"

        "Я не слишком уверен.":
            m 1eta "А, просто в предвкушении того, что будет дальше?{w=0.2} {nw}"
            extend 1eua "В предвкушении жизни?{w=0.2} {nw}"
            extend 1tsu "А может быть.{w=0.3}.{w=0.3}.{w=0.3}{nw}"
            m 1tku "Может быть, ты рад провести время со мной?~"
            m 1huu "Э-хе-хе~"
            m 3eua "Я знаю, я всегда рада видеть тебя каждый день."
            m 1hub "В любом случае, я рада, что ты счастлив!"
    return
