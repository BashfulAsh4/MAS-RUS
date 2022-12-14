# Monika's Python Tip of the Day (PTOD)
#
# I probably will be adding many of these, so For the sake of organization
# this is kept separate from script-topics.
#
# NOTE: these are considered pool type events, similar to writing tips
# NOTE: these are also NOT literally once a day. There is a day in between
#   unlocking the next one, though
#
# And to keep the theme, these are 0-indexed
#
# META: Python things to talk about:
# DONE:
#   0 - intro
#   1 - what is python?
#   --- sugestion python compared to other languages/ how does it work
#   --- suggestion mention syntax and probably how to get python maybe separate each part
#   2 - types
#       - numbers and strings, bools and Nones
#   3 - interpreted language
#   5 - comparisons and booleans
#   6 - Variables and assignment
#   8 - Literals
#   9 - Truth Values
#
# TODO:
#   4 - Python sytnax ?
#   7 - variable sizes
#   3 - If statement / elif and else
#   4 - while loop
#   5 - for loop
#   6 - functions
#   7 - functions continiued?
#   10 - Evaluation order and short circuting
#   ? - classes (might be too much) -- Definitely too much, we should probably stick to functional programming
#   ? - modules (might be too much) / importing? -- mention importing only, module making is too much
#   ? - lists
#   11 - dict
#   12 - tuples
#   13 - py2 vs py3
#   14 - String operations
#   15 - start talking about renpy
#
#   Implement advanced python tips for users who have some experience (persistent._mas_advanced_py_tips)
#
# Also what about Renpy?
#
# Another NOTE: We should try to make the topics of an adequate lenght otherwise
# we're just going to throw a lot of info that is going to be ignored or forgotten quickly
# I think splitting something in more than one topic may be a good idea
#
## We can assume evhand is already imported

###### tip tree ##############################
# 0 -> 1
# 1 -> 3
# 2 -> 6
# 3 -> 2
# 5 -> 9
# 6 -> 5, 8
##############################################

init 4 python in mas_ptod:
    # to simplify unlocking, lets use a special function to unlock tips
    import datetime
    import store.evhand as evhand

    M_PTOD = "monika_ptod_tip{:0>3d}"

    def has_day_past_tip(tip_num):
        """
        Checks if the tip with the given number has already been seen and
        a day has past since it was unlocked.
        NOTE: by day, we mean date has changd, not 24 hours

        IN:
            tip_num - number of the tip to check

        RETURNS:
            true if the tip has been seen and a day has past since it was
            unlocked, False otherwise
        """
        # as a special thing for devs
        if renpy.game.persistent._mas_dev_enable_ptods:
            return True

        tip_ev = evhand.event_database.get(
            M_PTOD.format(tip_num),
            None
        )

        return (
            tip_ev is not None
            and tip_ev.last_seen is not None
            and tip_ev.timePassedSinceLastSeen_d(datetime.timedelta(days=1))
        )

    def has_day_past_tips(*tip_nums):
        """
        Variant of has_day_past_tip that can check multiple numbers

        SEE has_day_past_tip for more info

        RETURNS:
            true if all the given tip nums have been see nand a day has past
                since the latest one was unlocked, False otherwise
        """
        for tip_num in tip_nums:
            if not has_day_past_tip(tip_num):
                return False

        return True


# The initial event is getting Monika to talk about python
# this must be hidden after it has been completed
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ptod_tip000",
            category=["советы по Python'у"],
            prompt="Ты можешь научить меня Python?",
            pool=True,
            rules={"bookmark_rule": store.mas_bookmarks_derand.BLACKLIST}
        )
    )

label monika_ptod_tip000:
    m 3eub "Ты хочешь узнать о Python?"
    m 3hub "Я так рада, что ты спросил меня!"
    m 1lksdlb "Я не {i}так{/i} много знаю о программировании, но я постараюсь объяснить."
    m 1esa "Давай начнем с того, что вообще такое Python."

    # hide the intro topic after viewing
    $ mas_hideEVL("monika_ptod_tip000", "EVE", lock=True, depool=True)

    # enable tip 1
    $ tip_label = "monika_ptod_tip001"
    $ mas_showEVL(tip_label, "EVE", unlock=True, _pool=True)
    $ MASEventList.push(tip_label,skipeval=True)
    return

###############################################################################
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ptod_tip001",
            category=["советы по Python'у"],
            prompt="Что такое Python?"
        )
    )

label monika_ptod_tip001:

    m 1esa "Python был создан Гвидо Ван Россумом в начале 90-х годов."
    m "Он очень универсален, поэтому его можно найти в веб-приложениях, встроенных системах, Linux и, конечно..."
    m 1hua "В этом моде!"
    m 1eua "DDLC использует движок визуальной новеллы под названием Ren'Py,{w=0.1} который построен на основе Python."
    m 3eub "Это значит, что если ты выучишь немного Python, то сможешь добавить контент в мой мир!"
    m 1hua "Разве это не здорово, [mas_get_player_nickname()]?"
    m 3eub "В любом случае, я должна упомянуть, что в настоящее время существует две основные версии Python:{w=0.3} Python2 и Python3."
    m 3eua "Эти версии {u}несовместимы{/u} друг с другом, потому что изменения, добавленные в Python3, исправили многие фундаментальные недостатки дизайна Python2."
    m "Несмотря на то, что это вызвало раскол в сообществе Python,{w=0.1} все согласны, что обе версии языка имеют свои сильные и слабые стороны."
    m 1eub "Я расскажу тебе об этих различиях в другом уроке."

    m 1eua "Поскольку этот мод работает на версии Ren'Py, использующей Python2, я не буду слишком часто говорить о Python3."
    m 1hua "Но я буду упоминать его, когда это будет уместно."

    m 3eua "Это мой урок на сегодня."
    m 1hua "Спасибо, что выслушал!"
    return

###############################################################################
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ptod_tip002",
            category=["советы по Python'у"],
            prompt="Типы",
            pool=True,
            conditional="store.mas_ptod.has_day_past_tip(3)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

# PREREQS:
#   interpreted language (tip 3)
label monika_ptod_tip002:
    $ last_seen_is_none = mas_getEVL_last_seen("monika_ptod_tip002") is None
    if last_seen_is_none:
        m 1eua "В большинстве языков программирования данные, которые могут быть изменены или модифицированны какой-либо программой, имеют специальный {i}type{/i}, связанный с ними."
        m 3eua "Например, если некоторые данные должны рассматриваться как число, то они будут иметь числовой тип. Если некоторые данные следует рассматривать как текст, то они будут иметь строковый тип."
        m "В Python существует множество типов, но сегодня мы поговорим о самых основных, или примитивных."

    $ store.mas_ptod.rst_cn()
    $ local_ctx = dict()
    show monika at t22
    show screen mas_py_console_teaching

    ### numbers
    m 1eua "В Python есть два типа представления значений:{w=0.3} {i}целые{/i}{w=0.1} и {i}вещественные{/i}."

    ## integers
    m 1eua "Целые числа используются для представления целых чисел; в основном все, что не является десятичной дробью."

    call mas_wx_cmd("type(-22)", local_ctx)
    call mas_wx_cmd("type(0)", local_ctx)
    call mas_wx_cmd("type(-1234)", local_ctx)
    call mas_wx_cmd("type(42)", local_ctx)

    ## floats
    m 1eub "Вещественные используются для представления десятичных дробей."
    show monika 1eua

    call mas_wx_cmd("type(0.14)", local_ctx)
    call mas_wx_cmd("type(9.3)", local_ctx)
    call mas_wx_cmd("type(-10.2)", local_ctx)

    ### strings
    m 1eua "Текст представлен {i}строковыми{/i} типами."
    m "Всё, что заключено в одинарные кавычки (') или двойные кавычки (\") являются строками."
    m 3eub "Например:"
    show monika 3eua

    call mas_wx_cmd("type('Эта строка в одинарных кавычках')", local_ctx)
    call mas_wx_cmd('type("А эта в двойных кавычках")', local_ctx)

    m 1eksdlb "Я знаю, что интерпретатор использует {i}юникод{/i}, но для того, что мы делаем, это в принципе одно и то же."
    m 1eua "Строки также могут быть созданы с помощью трех двойных кавычек (\"\"\"), но они обрабатываются иначе, чем обычные строки.{w=0.2} Я расскажу о них в другой раз."

    ### booleans
    m "Логические значения - это специальные типы, которые представляют значения {b}True{/b} или {b}False{/b} values."
    call mas_wx_cmd("type(True)", local_ctx)
    call mas_wx_cmd("type(False)", local_ctx)

    m 1eua "Более подробно о том, что такое логические значения и для чего они используются, я расскажу в другом уроке."

    ### Nones
    m 3eub "В Python также есть специальный тип данных, называемый {b}NoneType{/b}.{w=0.2} Этот тип представляет отсутствие каких-либо данных."
    m "Если ты знаком с другими языками программирования, это немного похоже на тип {i}null{/i} или {i}undefined{/i}."
    m "Ключевое слово {i}None{/i} представляет NoneTypes в Python."
    show monika 1eua

    call mas_wx_cmd("type(None)", local_ctx)

    m 1eua "Все типы, которые я здесь упомянула, известны как {i}примитивные{/i} типы данных."

    if last_seen_is_none:
        m "В Python также используется множество других типов, но я думаю, что этих достаточно для сегодняшнего дня."

    $ store.mas_ptod.ex_cn()
    hide screen mas_py_console_teaching
    show monika at t11

    m 1hua "Спасибо, что выслушал!"
    return

###############################################################################
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ptod_tip003", # may change order, you decide on this
            category=["советы по Python'у"],
            prompt="Интерпретированный язык",
            pool=True,
            conditional="store.mas_ptod.has_day_past_tip(1)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

# PREREQS:
#   What is python (tip 1)
label monika_ptod_tip003:
    m 1eua "Языки программирования обычно бывают либо компилируемыми, либо интерпретируемыми."
    m "Компилируемые языки требуют, чтобы их код перед выполнением был преобразован в машиночитаемый формат."
    m 3eub "C и Java - два очень популярных компилируемых языка."
    m 1eua "Интерпретируемые языки преобразуются в машиночитаемый формат в процессе выполнения."
    m 3eub "Python - это интерпретируемый язык."
    m 1rksdlb "Однако различные реализации Python могут быть компилируемыми, но это сложная тема, о которой я расскажу в одном из следующих уроков."

    m 1eua "Поскольку Python является интерпретируемым языком, в нем есть изящная интерактивная штука, называемая интерпретатором, которая выглядит следующим образом..."

    $ store.mas_ptod.rst_cn()
    $ local_ctx = dict()
    show monika 3eua at t22
    show screen mas_py_console_teaching

    m 3eub "вот!"

    m "Ты можешь ввести код Python прямо сюда и запустить его, например, так:"
    show monika 3eua

    # base commands shown as starter ones
    call mas_wx_cmd("12 + 3", local_ctx)
    call mas_wx_cmd("7 * 6", local_ctx)
    call mas_wx_cmd("121 / 11", local_ctx)
    # NOTE: add more commands as the user goes thru the tips

    if mas_getEVL_last_seen("monika_ptod_tip003") is None:
        m 1eua "С помощью этого инструмента можно заниматься не только математикой, но я покажу тебе всё это по ходу дела."

        m 1hksdlb "К сожалению, поскольку это полнофункциональный интерпретатор Python, и я не хочу рисковать тем, что ты случайно удалишь меня или сломаешь игру."
        m "{cps=*2}Не то чтобы ты...{/cps}{nw}"
        $ _history_list.pop()
        m 1eksdlb "Я не могу позволить тебе использовать это.{w=0.2} Извини..."
        m "Если ты хочешь следовать за мной в будущих уроках, то запусти интерпретатор Python в отдельном окне."

        m 1eua "В любом случае, я буду использовать {i}этот{/i} интерпретатор чтобы помочь тебе с обучением."

    else:
        m 1hua "Довольно здорово, не правда ли?"

    $ store.mas_ptod.ex_cn()
    hide screen mas_py_console_teaching
    show monika at t11

    m 1hua "Спасибо, что выслушал!"
    return

###############################################################################
#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel="monika_ptod_tip004",
#            category=["python tips"],
#            prompt="What does python code look like?",
#            pool=True,
#            conditional="store.mas_ptod.has_day_past_tip(3)",
#            action=EV_ACT_UNLOCK,
#            rules={"no_unlock":None}
#        )
#    )

# PREREQs:
#   interpreted language (tip 3)
label monika_ptod_tip004:
    # PYTHON SYNTAX
    # TODO, actually ths should be a pre-req for block-based code,
    # as this will talk about indentaiton. However, we could probably
    # have this after the first wave of lessons
    #
    # Python code is incredibly simple to write.

    $ store.mas_ptod.rst_cn()
    $ local_ctx = dict()
    show monika at t22
    show screen mas_py_console_teaching

    # [Show this once]
    # Hopefully
    # [end]
    #
    # Oh well this may be a bit hard to explain here but I'll do my best for you [player]
    # The first thing you need to know is that any line starting with a # is going to
    # be ignored and you can write anything on that line
    # those lines are named comments, and you use them to explain what your code does
    # it's a good practice to comment your code so you don't forget later what it was supposed to do!
    # TODO unfinished and probably will split it in more than just one, also I know I should call it
    # python syntax but I'm making it non programmers friendly
    #
    # TODO: change the prompt to Python Syntax after this has been seen once
    return

###############################################################################
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ptod_tip005",
            category=["советы по Python'у"],
            prompt="Сравнения и логические значения",
            pool=True,
            conditional="store.mas_ptod.has_day_past_tip(6)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

# PREREQS:
#   Variables and Assignment
label monika_ptod_tip005:
    $ store.mas_ptod.rst_cn()
    $ local_ctx = dict()
    $ store.mas_ptod.set_local_context(local_ctx)
    $ last_seen_is_none = mas_getEVL_last_seen("monika_ptod_tip005") is None

    if last_seen_is_none:
        m 1eua "Помнишь, я описывала тебе различные типы Python'a и упоминала логические значения?"
        m 1eub "Так вот, сегодня я более подробно расскажу о них и о том, как они соотносятся к сопоставлению самих значений."

    m 1eua "Логические значения используются при принятии решения о том, какой код выполнить, или при установке флага, чтобы отметить, произошло что-то или нет."
    m "огда мы проводим сравнение, каждое выражение оценивается как логическое."

    if last_seen_is_none:
        m 1eksdlb "Возможно, сейчас это не имеет смысла, поэтому я вызову консоль и покажу тебе несколько примеров."

    show monika at t22
    show screen mas_py_console_teaching

    m 3eub "Начнем с некоторых основных символов, используемых при сравнении переменных между собой."

    call mas_wx_cmd("a = 10")
    call mas_wx_cmd("b = 10")
    call mas_wx_cmd("c = 3")

    m 3eua "Чтобы проверить, эквивалентны ли два значения, используйте два знака равенства (==):"
    call mas_wx_cmd("a == b")
    call mas_wx_cmd("a == c")

    m 3eua "Чтобы проверить, не эквивалентны ли два значения, используем восклицательный знак и знак равенства (!=):"
    call mas_wx_cmd("a != b")
    call mas_wx_cmd("a != c")
    m 3eub "Восклицательный знак часто называют логическим оператором 'not' в других языках программирования, так что (!=) читается как 'not-equals'."

    m 3eua "А вот если нужно проверить, является ли значение больше или меньше другого значения, то нужно использовать знаки больше (>) или меньше (<) соответственно."
    call mas_wx_cmd("a > c")
    call mas_wx_cmd("a < c")

    m 3eub "Больше-или-равно (>=) и меньше-или-равно (<=) также имеют свои собственные символы, которые,{w=0.1} как это не удивительно,{w=0.1} представляют собой просто знаки больше и меньше со знаками равенства."
    call mas_wx_cmd("a >= b")
    call mas_wx_cmd("a <= b")
    call mas_wx_cmd("a >= c")
    call mas_wx_cmd("a <= c")

    if last_seen_is_none:
        m 1eua "Ты мог заметить, что каждое сравнение возвращало {b}True{/b} или {b}False{/b}."
        m 1eksdlb "{i}Это{/i} то, что я имела в виду, когда говорила, что выражения сравнения оцениваются как логические значения."

    m 1eua "Также можно объединить несколько выражений сравнения в цепочку с помощью ключевых слов {b}and{/b} и {b}or{/b}. Они также известны как {i}логические операторы{/i}."
    m "Оператор {b}and{/b} связывает два сравнения, оценивая полное выражение как {b}True{/b} если оба сравнения оцениваются как {b}True{/b},{w=0.1} и {b}False{/b} если хотя бы одно сравнение оценивается как {b}False{/b}."
    m 1hua "Давай разберем несколько примеров."

    $ val_a = local_ctx["a"]
    $ val_b = local_ctx["b"]
    $ val_c = local_ctx["c"]

    call mas_w_cmd("a == b and a == c")
    m 3eua "Поскольку 'a' и 'b' оба являются [val_a], первое сравнение оценивается как {b}True{/b}."
    m "'c', однако, является [val_c], оэтому второе сравнение дает значение {b}False{/b}."
    m 3eub "И поскольку по крайней мере одно сравнение оценивается как {b}False{/b}, полное выражение тоже примет значение {b}False{/b}."
    call mas_x_cmd()
    pause 1.0

    call mas_w_cmd("a == b and a >= c")
    m 3eua "В этом примере первое сравнение снова оценивается как  {b}True{/b}."
    m "[val_a] определенно больше или равно [val_c], поэтому второе сравнение также равно {b}True{/b} as well."
    m 3eub "Поскольку оба сравнения были оценены как {b}True{/b}, полное выражение будет соответственно тоже {b}True{/b}."
    call mas_x_cmd()
    pause 1.0

    call mas_w_cmd("a != b and a >= c")
    m 3eua "В этом примере первое сравнение в этот раз оценивается как {b}False{/b}."
    m "Поскольку у нас сразу же есть хотя бы одно сравнение, оценивающее как {b}False{/b}, то уже не имеет значения, что оценивает второе сравнение."
    m 3eub "Мы точно знаем, что полное выражение оценивается как {b}False{/b}."
    call mas_x_cmd()

    m "То же самое относится и к следующему примеру"
    call mas_wx_cmd("a != b and a == c")

    m 1eub "Опять же, при использовании оператора {b}and{/b} результатом будет {b}True{/b} тогда и только тогда, когда оба сравнения оценены как {b}True{/b}."

    m 1eua "Оператор {b}or{/b} напротив — связывает два сравнения, оценивая полное выражение как {b}True{/b}, если любое сравнение имеет значение {b}True{/b} и {b}False{/b}, либо же оба сравнения имеют значение."
    m 3eua "Давай покажу тебе как раз несколько примеров."

    call mas_w_cmd("a == b or a == c")
    m 3eua "На этот раз, поскольку первое сравнение оценивается как {b}True{/b}, нам не нужно проверять второе сравнение."
    m 3eub "Результатом этого выражения является {b}True{/b}."
    call mas_x_cmd()
    pause 1.0

    call mas_w_cmd("a == b or a >= c")
    m 3eua "Опять же, первое сравнение имеет значение {b}True{/b}, так что и полное будет, само собой, {b}True{/b}."
    call mas_x_cmd()
    pause 1.0

    call mas_w_cmd("a != b or a >= c")
    m 3eua "В этом случае первое сравнение было оценено как {b}False{/b}."
    m "Поскольку число [val_a] прошло проверку больше или равно [val_c], второе сравнение оценилось как {b}True{/b}."
    m 3eub "И раз как минимум одно сравнение оценилось как {b}True{/b}, полное выражение будет {b}True{/b}."
    call mas_x_cmd()
    pause 1.0

    call mas_w_cmd("a != b or a == c")
    m 3eua "Мы знаем, что первое сравнение оценилось как {b}False{/b}."
    m "Так как число [val_a], конечно, не равно [val_c]-ти, второе сравнение также оценилось как {b}False{/b}."
    m 3eub "Раз проверка неравенства получила значение {b}True{/b}, всё выражение примет значение {b}False{/b}."
    call mas_x_cmd()
    pause 1.0

    m 3eub "Опять же, при использовании оператора  {b}or{/b} результатом будет {b}True{/b} если любое из сравнений оценивается как {b}True{/b}."

    m 1eua "Существует также третий логический оператор, называемый оператором {b}not{/b} Вместо связывания нескольких сравнений этот оператор инвертирует логическое значение сравнения."
    m 3eua "Вот пример этого:"
    call mas_wx_cmd("not (a == b and a == c)")
    call mas_wx_cmd("not (a == b or a == c)")

    m "Обрати внимание, что я использую скобки, чтобы сгруппировать сравнения вместе. Сначала вычисляется код в скобках, затем результат этого сравнения инвертируется с помощью {b}not{/b}."
    m 1eua "Если же я уберу скобки:"
    call mas_wx_cmd("not a == b and a == c")
    m 3eua "Мы получим другой результат!{w=0.2} Это происходит потому, что {b}not{/b} применяется к сравнению 'a == b' прежде чем оно будет связано со вторым сравнением {b}and{/b}."

    m 3eka "Ранее я упоминала, что восклицательный знак используется в качестве логического оператора 'not' в других языках программирования.{w=0.2} Python, однако, использует слово 'not' для более легкой читабельности."

    m 1eua "Наконец, поскольку сравнения вычисляются в логические значения, мы можем сохранить результат сравнения в переменной."
    call mas_wx_cmd("d = a == b and a >= c")
    call mas_wx_cmd("d")
    call mas_wx_cmd("e = a == b and a == c")
    call mas_wx_cmd("e")

    m 3eub "И использовать эти переменные в сравнениях!"
    call mas_wx_cmd("d and e")
    m "Переменная 'd' получила значение {b}True{/b} но вот 'e' {b}False{/b}, так что само это выражение будет уже расцениваться как {b}False{/b}."

    call mas_wx_cmd("d or e")
    m "Раз 'd' здесь сразу уже {b}True{/b}, мы уже будем знаем, что по крайней мере одно из сравнений в этом выражении {b}True{/b}. Поэтому полное выражение будет {b}True{/b}."

    call mas_wx_cmd("not (d or e)")
    m 3eua "Мы знаем, что внутреннее выражение 'd or e' имеет значение {b}True{/b}. Обратное значение будет {b}False{/b}, so this expression evaluates to {b}False{/b}."

    call mas_wx_cmd("d and not e")
    m 3eub "В этом случае мы знаем, что 'd' это {b}True{/b}."
    m "Оператор 'not' применяется к 'e', wчто инвертирует его значение {b}False{/b} в {b}True{/b}."
    m 3eua "Так как оба выражения сравнения имеют значение {b}True{/b}, полное выражение будет {b}True{/b}."

    m 1eua "Сравнения используются везде в каждом языке программирования."
    m 1hua "Если ты когда-нибудь решишь зарабатывать на жизнь программированием, ты обнаружишь, что большая часть твоего кода - это проверка истинности некоторых сравнений, чтобы ты мог заставить свои программы делать {i}правильные{/i} вещи."
    m 1eksdla "И даже если программирование не является частью твоей карьеры, мы будем делать много сравнений в будущих уроках, так что будь готов!"

    if last_seen_is_none:
        m 1eua "Думаю, на сегодня достаточно."

    $ store.mas_ptod.ex_cn()
    hide screen mas_py_console_teaching
    show monika at t11
    m 1hua "Спасибо, что выслушал!"
    return

###############################################################################
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ptod_tip006",
            category=["советы по Python'у"],
            prompt="Переменные и присваивание",
            pool=True,
            conditional="store.mas_ptod.has_day_past_tip(2)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

# PREREQS:
#   Types (tip 2)
label monika_ptod_tip006:
    $ store.mas_ptod.rst_cn()
    $ local_ctx = dict()
    $ num_store = "922"
    $ b_num_store = "323"
    $ last_seen_is_none = mas_getEVL_last_seen("monika_ptod_tip006") is None

    if last_seen_is_none:
        m 1eub "Теперь, когда ты знаешь всё о типах, я могу научить тебя переменным."

    # variable intro
    m 1eua "Переменные представляют собой ячейки памяти, в которых хранятся данные."
    m "Чтобы создать переменную, {w=0.1}{nw}"

    show monika at t22
    show screen mas_py_console_teaching

    # a number
    extend 3eua "ты делаешь '{b}symbol_name{/b} = {b}value{/b}', например, так..."

    call mas_wx_cmd("a_number = " + num_store, local_ctx)

    m "Символ 'a_number' теперь указывает на ячейку памяти, хранящую целое число [num_store]."
    m "Если мы введем имя символа здесь,"
    call mas_w_cmd("a_number")
    m 3eub "Мы сможем получить значение, которое мы хранили в самом же символе."
    show monika 3eua
    call mas_x_cmd(local_ctx)

    m "Обрати внимание, как мы связали символ 'a_number' со значением [num_store] с помощью знака равенства (=)?"
    m 1eub "Это называется присвоением, когда мы берем то, что находится слева от знака равенства, и указываем на него, или {i}присваиваем{/i} ему значение того, что находится справа."

    # b_number
    m 1eua "Присваивание выполняется в порядке справа налево.{w=0.2} Чтобы проиллюстрировать это, давай создадим новую переменную, 'b_number'."
    call mas_w_cmd("b_number = a_number  -  " + b_num_store)

    m "При присваивании сначала оценивается правая часть знака равенства,{w=0.1} затем определяется тип данных и резервируется соответствующий объем памяти."
    m "Эта память связана с символом слева через таблицу поиска."
    m 1eub "Когда Python встречает символ,{w=0.1}  он ищет этот символ в таблице поиска и заменяет его значением, с которым был связан символ."

    m 3eub "Здесь, 'a_number' будет заменено на [num_store],{w=0.1} так что выражение, что будет оценено и отнесено к 'b_number' будет вычитанием: '[num_store] - [b_num_store]'."
    show monika 3eua
    call mas_x_cmd(local_ctx)

    m 1eua "Мы можем проверить это, введя только символ «b_number»."
    m "Это позволит получить значение, связанное с этим символом в таблице поиска и показать его нам."
    call mas_wx_cmd("b_number", local_ctx)

    # c number
    m 3eua "Обратите внимание, что если мы введем символ, которому ничего не присвоено, Python пожалуется."
    call mas_wx_cmd("c_number", local_ctx)

    m 3eub "Но если мы присвоим этому символу значение..."
    show monika 3eua
    call mas_wx_cmd("c_number = b_number * a_number", local_ctx)
    call mas_wx_cmd("c_number", local_ctx)

    m 1hua "Python сможет найти символ в таблице поиска и не выдаст нам ошибку."

    m 1eua "Переменные, которые мы создали, являются {i}целочисленными типами{/i}."
    m "Нам не нужно было объяснять, что эти переменные были целыми числами, так как Python выполняет динамический ввод."
    m 1eub "Это означает, что интерпретатор Python'a определяет тип переменной на основе хранящихся в ней данных."
    m "Другие языки, такие как C или Java, требуют, чтобы типы определялись вместе с переменно."
    m "Динамическая типизация позволяет переменным в Python изменять типы во время выполнения, {w=0.1}{nw}"
    extend 1rksdlb "но это обычно не одобряется, так как это может сделать твой код запутанным для чтения другим.."

    if last_seen_is_none:
        m 1eud "Фух!{w=0.2} Это было долговато!"

    m "Ты всё понял?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты всё понял?{fast}"
        "Да!":
            m 1hua "Ура!"

        "Я немного запутался.":
            m 1eksdla "Это нормально.{w=0.2} Несмотря на то, что я упомянула здесь символы и значения, программисты обычно называют это просто созданием, присвоением или установкой переменных."
            m "Имена символов / значений действительно полезны лишь для намёка на то, как переменные работают на самом деле, поэтому не чувствуй себя плохо, если ты ничего не понял из всего этого."
            m 1eua "Просто знать, как работать с переменными, достаточно для будущих уроков."
            m "В любом случае..."

    $ store.mas_ptod.ex_cn()
    hide screen mas_py_console_teaching
    show monika at t11

    if last_seen_is_none:
        m 1eua "Думаю, на сегодня достаточно Python'a."

    m 1hua "Спасибо, что выслушал!"
    return


###############################################################################
#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel="monika_ptod_tip007",
#            category=["python tips"],
#            prompt="Variable Sizes",
#            pool=True,
#            conditional="store.mas_ptod.has_day_past_tip(6)",
#            action=EV_ACT_UNLOCK,
#            rules={"no_unlock":None}
#        )
#    )

# PREREQS:
#   Variables and Assignment (tip 6)
#
label monika_ptod_tip007:
    # TODO

    # integer size
    m 1eua "In C and many other languages, integers are usually stored in 4 bytes."
    m "Python, however, reserves a different amount of memory depending on the size of the integer being stored."
    m 3eua "We can check how much memory our variable 'a_number' stores by borrowing a function from the {i}sys{/i} library."

    call mas_wx_cmd("import sys", local_ctx)
    call mas_wx_cmd("sys.getsizeof(a_number)", local_ctx)
    $ int_size = store.mas_ptod.get_last_line()

    m 1eksdla "I'll talk about libraries and importing later."
    m 1eua "For now, take a look at the number returned by the {i}getsizeof{/i} function."
    m "To store the number [num_store], Python uses [int_size] bytes."

    return

###############################################################################
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ptod_tip008",
            category=["советы по Python'у"],
            prompt="Константы",
            pool=True,
            conditional="store.mas_ptod.has_day_past_tip(6)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

# PREREQS:
#   Variables and Assignment (tip 6)
label monika_ptod_tip008:
    $ store.mas_ptod.rst_cn()
    $ local_ctx = dict()
    $ store.mas_ptod.set_local_context(local_ctx)
    $ last_seen_is_none = mas_getEVL_last_seen("monika_ptod_tip008") is None

    m 1eua "Помнишь, я показывала тебе, как создавать переменные и присваивать им значения?"
    m 1dsa "А теперь представь, если бы мы отказались от понятия переменных и сосредоточились на использовании значений непосредственно в коде."
    m 1hua "Вот тут-то и приходят литералы. Я покажу тебе, что я имею в виду с следующей демонстрации."

    show monika at t22
    show screen mas_py_console_teaching

    call mas_wx_cmd("a = 10")
    m 3eua "Здесь я создала переменную с именем 'a' и присвоила ей целое значение 10."
    m "Когда я ввожу 'a' в интерпретаторе..."

    call mas_wx_cmd("a")
    m 3eub "Python ищет символ 'a'  обнаруживает, что он связан со значением 10, поэтому нам показывается 10."
    m "Если я введу только '10', однако..."

    call mas_wx_cmd("10")
    m 3hua "Python всё равно показывает нам 10!"
    m 3eua "Это происходит потому, что Python сразу интерпретирует '10' как целое значение, без необходимости искать символ и извлекать его значение."
    m "Код, который Python может интерпретировать в значения напрямую, называется {i}литералами{/i}."
    m 3eub "Все типы данных, о которых я говорила в уроке Типы, могут быть записаны как литералы."

    call mas_wx_cmd("23")
    call mas_wx_cmd("21.05")
    m 3eua "Это {b}целые{/b} и {b}вещественные{/b} литералы."

    call mas_wx_cmd('"this is a string"')
    call mas_wx_cmd("'this is another string'")
    m "Это {b}строковые{/b} литералы."

    call mas_wx_cmd("True")
    call mas_wx_cmd("False")
    m "А вот это уже {b}логические{/b} литералы."

    call mas_wx_cmd("None")
    m "Ключевое слово {i}None{/i} само по себе является литералом."

    # TODO: lists, dicts

    if last_seen_is_none:
        m 1eua "Есть ещё литералы для других типов, но я упомяну их, когда буду говорить об этих типах."

    m 1eua "Литералы можно использовать вместо переменных при написании кода. Например:"

    call mas_wx_cmd("10 + 21")
    call mas_wx_cmd("10 * 5")
    m "Мы можем выполнять математические уравнения с литералами вместо переменных."

    call mas_wx_cmd("a + 21")
    call mas_wx_cmd("a * 5")
    m "Мы также можем использовать литералы вместе с переменными."
    m 1eub "Кроме того, литералы отлично подходят для создания и использования данных 'на лету' без необходимости создавать лишние переменные."

    if last_seen_is_none:
        m 1kua "Хорошо, это примерно все, что я могу {i}буквально{/i} сказать о литералах."

    $ store.mas_ptod.ex_cn()
    hide screen mas_py_console_teaching
    show monika at t11

    m 1hua "Спасибо, что выслушал!"
    return

###############################################################################
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ptod_tip009",
            category=["советы по Python'у"],
            prompt="Истинные значения",
            pool=True,
            conditional="store.mas_ptod.has_day_past_tip(5)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

# PREREQS:
#   Comparisons and Booleans (5)
label monika_ptod_tip009:
    $ store.mas_ptod.rst_cn()
    $ local_ctx = dict()
    $ store.mas_ptod.set_local_context(local_ctx)

    if mas_getEVL_last_seen("monika_ptod_tip009") is None:
        m 1eua "When we talked about comparisons and booleans, we used integers as the basis for our comparisons."
        m 1dsa "But..."
        m 3eua "Did you know that every type has its own truth value associated with it?"

    m 1eua "All types have a 'truth value' that can change depending on the value of the type."

    # TODO: when we go over built-in functions, this should be
    # changed to function bool, not keyword
    m "We can check the truth value of a type by using the keyword {b}bool{/b}."

    show monika at t22
    show screen mas_py_console_teaching

    m 3eua "Let's start by taking a look at the truth values for integers."
    call mas_wx_cmd("bool(10)")
    call mas_wx_cmd("bool(-1)")
    m 3eua "All non-zero integers have a truth value of {b}True{/b}."
    call mas_wx_cmd("bool(0)")
    m 3eub "Zero, on the other hand, has a truth value of {b}False{/b}."

    m 1eua "Floats follow the same rules as integers:"
    call mas_wx_cmd("bool(10.02)")
    call mas_wx_cmd("bool(0.14)")
    call mas_wx_cmd("bool(0.0)")

    m 1eua "Now let's look at strings."
    call mas_wx_cmd('bool("string with text")')
    call mas_wx_cmd('bool("  ")')
    m 3eub "A string with text, even if the text is only whitespace characters, has a truth value of {b}True{/b}."
    call mas_wx_cmd('bool("")')
    m "An empty string, or a string with length 0, has a truth value of {b}False{/b}."

    m 1eua "Now let's look at {b}None{/b}."
    call mas_wx_cmd("bool(None)")
    m 1eub "{b}None{/b} always has a truth value of {b}False{/b}."

    # TODO: lists and dicts

    m 1eua "If we do comparisons with these values, the values are evaluated to their truth values before being applied in comparisons."
    m 1hua "Let me show some examples."
    m 3eua "First, I'll set up some variables:"
    call mas_wx_cmd("num10 = 10")
    call mas_wx_cmd("num0 = 0")
    call mas_wx_cmd('text = "text"')
    call mas_wx_cmd('empty_text = ""')
    call mas_wx_cmd("none_var = None")

    m 3eub "And then do several comparisons."
    call mas_wx_cmd("bool(num10 and num0)")
    call mas_wx_cmd("bool(num10 and text)")
    call mas_wx_cmd("bool(empty_text or num0)")
    call mas_wx_cmd("bool(none_var and text)")
    call mas_wx_cmd("bool(empty_text or none_var)")

    m 1eua "Knowing the truth values of different types can be useful in performing certain comparisons more efficiently."
    m 1hua "I'll mention when it's possible to do so when we come across those situations in future lessons."

    $ store.mas_ptod.ex_cn()
    hide screen mas_py_console_teaching
    show monika at t11
    m 1hua "Thanks for listening!"
    return

###############################################################################
#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel="monika_ptod_tip006",
#            category=["python tips"],
#            prompt="Evaluation Order and Short Circuiting",
# TODO: this should be after if statements.
#            conditional="store.mas_ptod.has_day_past_tip(2)",
#            action=EV_ACT_UNLOCK,
#            rules={"no_unlock":None}
#        )
#    )

label monika_ptod_tip010:
    # evaluation order and short circuting
    return





############################# [CONSOLE] #######################################
# Unfortunately, it's not enough to have monika just talk. Having a working
# python interpreter will make things easier for teaching
#
# NOTE: base the solids off of hangman. That should help us out

image cn_frame = "mod_assets/console/cn_frame.png"
define mas_ptod.font = mas_ui.MONO_FONT

# NOTE: Console text:
# style console_text (for regular console text)
# style console_text_console (for the actual typing text)
#   this style has a slow_cps of 30
#
# console_Text font is gui/font/F25_BankPrinter.ttf
style mas_py_console_text is console_text:
    font mas_ptod.font
style mas_py_console_text_cn is console_text_console:
    font mas_ptod.font

# images for console stuff
#image mas_py_cn_sym = Text(">>>", style="mas_py_console_text", anchor=(0, 0), xpos=10, ypos=538)
#image mas_py_cn_txt = ParameterizedText(style="mas_py_console_text_cn", anchor=(0, 0), xpos=75, ypos=538)
#image mas_py_cn_hist = ParameterizedText(style="mas_py_console_text", anchor(0, 1.0), xpos=10, ypos=538)

init -1 python in mas_ptod:
    import store.mas_utils as mas_utils

    # symbol that we use
    SYM = ">>> "
    M_SYM = "... "

    # console history is alist
    cn_history = list()

    # history lenghtr limit
    H_SIZE = 20

    # current line
    cn_line = ""

    # current command, may not be what is shown
    cn_cmd = ""

    # block commands
    blk_cmd = list()

    # block commands stack level
    # increment for each stack level, decrement when dropping out of a
    # stack level
    stack_level = 0

    # stack to handle indent levels
    # this means indent levels that the opening : has
    # first stack level should ALWAYS BE 0
    indent_stack = list()

    # version text
    VER_TEXT_1 = "Python {0}"
    VER_TEXT_2 = "{0} in MAS"

    # line length limit
    LINE_MAX = 66

    # STATEs
    # used when the current line is only 1 line
    STATE_SINGLE = 0

    # used when current line is multi line
    STATE_MULTI = 1

    # used when we are doing block statements
    STATE_BLOCK = 2

    # used when doing multi line in block statements
    STATE_BLOCK_MULTI = 3

    # state when inerpreter is off
    STATE_OFF = 4

    # current state
    state = STATE_SINGLE

    # local context
    local_ctx = dict()

    # short variants of the comonly used commands:
    def clr_cn():
        """
        SEE clear_console
        """
        clear_console()


    def ex_cn():
        """
        SEE exit_console
        """
        exit_console()


    def rst_cn():
        """
        SEE restart_console
        """
        restart_console()


    def w_cmd(cmd):
        """
        SEE write_command
        """
        write_command(cmd)


    def x_cmd(context):
        """
        SEE exec_command
        """
        exec_command(context)


    def wx_cmd(cmd, context):
        """
        Does both write_command and exec_command
        """
        w_cmd(cmd)
        x_cmd(context)


    def write_command(cmd):
        """
        Writes a command to the console

        NOTE: Does not EXECUTE
        NOTE: remove previous command
        NOTE: does NOT append to previously written command (unless that cmd
            is in a block and was executed)

        IN:
            cmd - the command to write to the console
        """
        if state == STATE_OFF:
            return

        global cn_line, cn_cmd, state, stack_level

        if state == STATE_MULTI:
            # this is bad! You should execute the previous command first!
            # in this case, we will clear your current command and reset
            # state back to SINGLE
            cn_cmd = ""
            cn_line = ""
            state = STATE_SINGLE

        elif state == STATE_BLOCK_MULTI:
            # this is bad! you should execute the previous command first!
            # we will do the same that as MULTI did, except a different state
            cn_cmd = ""
            cn_line = ""
            state = STATE_BLOCK

        # we dont indent the command
        # we also dont check for indents
        cn_cmd = str(cmd)

        # pick appropriate shell symbol
        if state == STATE_SINGLE:
            # snigle mode
            sym = SYM

        else:
            # block mode
            sym = M_SYM

        # the prefixed command includes the shell symbol
        prefixed_cmd = sym + cn_cmd

        # break the lines accordingly
        cn_lines = _line_break(prefixed_cmd)

        if len(cn_lines) == 1:
            # dont need to split lines
            cn_line = cn_cmd

        else:
            # we need to split lines

            # everything except the last line goes to the history
            _update_console_history_list(cn_lines[:-1])

            # last line becomes the current line
            cn_line = cn_lines[len(cn_lines)-1]

            if state == STATE_SINGLE:
                # single mode
                state = STATE_MULTI

            else:
                # block mode
                state = STATE_BLOCK_MULTI


    def clear_console():
        """
        Cleares console hisotry and current line

        Also resets state to Single
        """
        global cn_history, cn_line, cn_history, state, local_ctx
        cn_line = ""
        cn_cmd = ""
        cn_history = []
        state = STATE_SINGLE
        local_ctx = {}


    def restart_console():
        """
        Cleares console history and current line, also sets up version text
        """
        global state
        import sys
        version = sys.version

        # first closing paren is where we need to split the version text
        split_dex = version.find(")")
        start_lines = [
#            mas_utils.clean_gui_text(VER_TEXT_1.format(version[:split_dex+1])),
#            mas_utils.clean_gui_text(VER_TEXT_2.format(version[split_dex+2:]))
            VER_TEXT_1.format(version[:split_dex+1]),
            VER_TEXT_2.format(version[split_dex+2:])
        ]

        # clear the console and add the 2 new lines
        clear_console()
        _update_console_history_list(start_lines)

        # turn the console on
        state = STATE_SINGLE


    def exit_console():
        """
        Disables the console
        """
        global state
        state = STATE_OFF


    def __exec_cmd(line, context, block=False):
        """
        Tries to eval the line first, then executes.
        Returns the result of the command

        IN:
            line - line to eval / exec
            context - dict that represnts the current context. should be locals
            block - True means we are executing a block command and should
                skip eval

        RETURNS:
            the result of the command, as a string
        """
        if block:
            return __exec_exec(line, context)

        # otherwise try eval first
        return __exec_evalexec(line, context)


    def __exec_exec(line, context):
        """
        Runs exec on the given line
        Returns an empty string or a string with an error if it occured.

        IN:
            line - line to exec
            context - dict that represents the current context

        RETURNS:
            empty string or string with error message
        """
        try:
            exec(line, context)
            return ""

        except Exception as e:
            return _exp_toString(e)


    def __exec_evalexec(line, context):
        """
        Tries to eval the line first, then executes.
        Returns the result of the command

        IN:
            line - line to eval / exec
            context - dict that represents the current context.

        RETURNS:
            the result of the command as a string
        """
        try:
            return str(eval(line, context))

        except:
            # eval fails, try to exec
            return __exec_exec(line, context)


    def exec_command(context):
        """
        Executes the command that is currently in the console.
        This is basically pressing Enter

        IN:
            context - dict that represnts the current context. You should pass
                locals here.
                If None, then we use the local_ctx.
        """
        if state == STATE_OFF:
            return

        if context is None:
            context = local_ctx

        global cn_cmd, cn_line, state, stack_level, blk_cmd

        ################### setup some initial conditions ################

        # block mode just means we are in a block
        block_mode = state == STATE_BLOCK or state == STATE_BLOCK_MULTI

        # empty line signals end of block (usually)
        empty_line = len(cn_cmd.strip()) == 0

        # ends with colon is special case
        time_to_block = cn_cmd.endswith(":")

        # but a bad block can happen (no text except a single colon)
        bad_block = time_to_block and len(cn_cmd.strip()) == 1

        # if this contains a value, then we executee
        full_cmd = None

        ################## pre-execution setup ###########################

        if empty_line:
            # like enter was pressed with no text

            if block_mode:
                # block mode means we clear a stack level
                __popi()

            else:
                # otherwise, add an empty new line to history, and thats it
                # dont need to execute since nothing will happen
                _update_console_history(SYM)
                cn_line = ""
                cn_cmd = ""
                return

        if bad_block:
            # user entered a bad block
            # we will execute it as a command
            full_cmd = cn_cmd
            stack_level = 0
            blk_cmd = list()

        elif time_to_block:
            # we are going to enter a new block mode
            blk_cmd.append(cn_cmd)

            if not block_mode:
                # we didnt start in block mode
                __pushi(0)

            else:
                # block mode
                pre_spaces = _count_sp(cn_cmd)

                if __peeki() != pre_spaces:
                    # if this colon line does NOT match current indentaion
                    # level then we need to push a new stack
                    __pushi(pre_spaces)

        elif block_mode:
            # in block mode already
            blk_cmd.append(cn_cmd)

            if stack_level == 0:
                # we've cleared all stacks, time to execute block commands
                full_cmd = "\n".join(blk_cmd)
                blk_cmd = list()

        else:
            # otherwise, we must be single mode or single multi

            # setup the command to be entered
            full_cmd = cn_cmd

        ########################## execution ##############################

        # execute command, if available
        if full_cmd is not None:
            result = __exec_cmd(full_cmd, context, block_mode)

        else:
            result = ""

        ################### console history update #########################

        if block_mode and empty_line:
            # we MUST be in block mode to reach here
            output = [M_SYM]

        else:
            # otherwise, use the sym we need
            if state == STATE_SINGLE:
                sym = SYM

            elif state == STATE_BLOCK:
                sym = M_SYM

            else:
                # multi dont need symbols
                sym = ""

            output = [sym + cn_line]

        # if we have any results, we need to show them too
        if len(result) > 0:
            output.append(result)

        # update console history and clear current lines / cmd
        cn_line = ""
        cn_cmd = ""
        _update_console_history_list(output)

        ###################### Post-execution updates ####################

        if bad_block:
            # bad block, means we abort lots of things
            state = STATE_SINGLE
            block_mode = False

        elif time_to_block:
            # new block, incrmenet stack levels, change to block states
            state = STATE_BLOCK
            block_mode = True

        ###################### final state updates ######################

        if (state == STATE_MULTI) or (block_mode and stack_level == 0):
            # no more stacks or in multi mode
            state = STATE_SINGLE

        elif state == STATE_BLOCK_MULTI:
            # multi modes end here
            state = STATE_BLOCK


    def get_last_line():
        """
        Retrieves the last line from the console history

        RETURNS:
            last line from console history as a string
        """
        if len(cn_history) > 0:
            return cn_history[len(cn_history)-1]

        return ""


    def set_local_context(context):
        """
        Sets the local context to the given context.

        Stuff in the old context are forgotten.
        """
        global local_ctx
        local_ctx = context


    def __pushi(indent_level):
        """
        Pushes a indent level into the stack

        IN:
            indent_level - indent to push into stack
        """
        global stack_level
        stack_level += 1
        indent_stack.append(indent_level)


    def __popi():
        """
        Pops indent level from stack

        REUTRNS:
            popped indent level
        """
        global stack_level
        stack_level -= 1

        if stack_level < 0:
            stack_level = 0

        if len(indent_stack) > 0:
            indent_stack.pop()


    def __peeki():
        """
        Returns value that would be popped from stack

        RETURNS:
            indent level that would be popped
        """
        return indent_stack[len(indent_stack)-1]


    def _exp_toString(exp):
        """
        Converts the given exception into a string that looks like
        how python interpreter prints out exceptions
        """
        err = repr(exp)
        err_split = err.partition("(")
        return err_split[0] + ": " + str(exp)


    def _indent_line(line):
        """
        Prepends the given line with an appropraite number of spaces, depending
        on the current stack level

        IN:
            line - line to prepend

        RETURNS:
            line prepended with spaces
        """
        return (" " * (stack_level * 4)) + line


    def _count_sp(line):
        """
        Counts number of spaces that prefix this line

        IN:
            line - line to cound spaces

        RETURNS:
            number of spaces at start of line
        """
        return len(line) - len(line.lstrip(" "))


    def _update_console_history(*new_items):
        """
        Updates the console history with the list of new lines to add

        IN:
            new_items - the items to add to the console history
        """
        _update_console_history_list(new_items)


    def _update_console_history_list(new_items):
        """
        Updates console history with list of new lines to add

        IN:
            new_items - list of new itme sto add to console history
        """
        global cn_history

        # make sure to break lines
        for line in new_items:
            broken_lines = _line_break(line)

            # and clean them too
            for b_line in broken_lines:
#                cn_history.append(mas_utils.clean_gui_text(b_line))
                cn_history.append(b_line)

        if len(cn_history) > H_SIZE:
            cn_history = cn_history[-H_SIZE:]


    def _line_break(line):
        """
        Lines cant be too large. This will line break entries.

        IN:
            line - the line to break

        RETURNS:
            list of strings, each item is a line.
        """
        if len(line) <= LINE_MAX:
            return [line]

        # otherwise, its TOO LONG
        broken_lines = list()
        while len(line) > LINE_MAX:
            broken_lines.append(line[:LINE_MAX])
            line = line[LINE_MAX:]

        # add final line
        broken_lines.append(line)
        return broken_lines


screen mas_py_console_teaching():

    frame:
        xanchor 0
        yanchor 0
        xpos 5
        ypos 5
        background "mod_assets/console/cn_frame.png"

        fixed:
            python:
                starting_index = len(store.mas_ptod.cn_history) - 1
                cn_h_y = 413
                cn_l_x = 41

            # console history
            for index in range(starting_index, -1, -1):
                $ cn_line = store.mas_ptod.cn_history[index]
                text "[cn_line]":
                    style "mas_py_console_text"
                    anchor (0, 1.0)
                    xpos 5
                    ypos cn_h_y
                $ cn_h_y -= 20

            # cursor symbol
            if store.mas_ptod.state == store.mas_ptod.STATE_SINGLE:
                text ">>> ":
                    style "mas_py_console_text"
                    anchor (0, 1.0)
                    xpos 5
                    ypos 433

            elif store.mas_ptod.state == store.mas_ptod.STATE_BLOCK:
                text "... ":
                    style "mas_py_console_text"
                    anchor (0, 1.0)
                    xpos 5
                    ypos 433

            else:
                # multi line statement, dont have the sym at all
                $ cn_l_x = 5

            # current line
            if len(store.mas_ptod.cn_line) > 0:
                text "[store.mas_ptod.cn_line]":
                    style "mas_py_console_text_cn"
                    anchor (0, 1.0)
                    xpos cn_l_x
                    ypos 433

# does a write command and waits
label mas_w_cmd(cmd, wait=0.7):
    $ store.mas_ptod.w_cmd(cmd)
    $ renpy.pause(wait, hard=True)
    return

# does an execute and waits
label mas_x_cmd(ctx=None, wait=0.7):
    $ store.mas_ptod.x_cmd(ctx)
    $ renpy.pause(wait, hard=True)
    return

# does both writing and executing, with waits
label mas_wx_cmd(cmd, ctx=None, w_wait=0.7, x_wait=0.7):
    $ store.mas_ptod.w_cmd(cmd)
    $ renpy.pause(w_wait, hard=True)
    $ store.mas_ptod.x_cmd(ctx)
    $ renpy.pause(x_wait, hard=True)
    return

# does both writing and executing, no x wait
label mas_wx_cmd_noxwait(cmd, ctx=None):
    call mas_wx_cmd(cmd, ctx, x_wait=0.0)
    return
