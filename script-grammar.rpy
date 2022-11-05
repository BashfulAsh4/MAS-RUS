# Monika's Grammar Tip of the Day (GTOD)
# TIPS
# 0 - Intro
# 1 - Clauses
# 2 - Comma Splices/Run-ons
# 3 - Conjunctions
# 4 - Semicolons
# 5 - Subjects and Objects
# 6 - Active and Passive Voices
# 7 - Who vs. Whom
# 8 - And I vs. And me
# 9 - Apostrophes
# 10 - The Oxford Comma

init 4 python in mas_gtod:
    # to simplify unlocking, lets use a special function to unlock tips
    import datetime
    import store.evhand as evhand

    M_GTOD = "monika_gtod_tip{:0>3d}"

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

        tip_ev = evhand.event_database.get(
            M_GTOD.format(tip_num),
            None
        )

        return (
            tip_ev is not None
            and tip_ev.last_seen is not None
            and tip_ev.timePassedSinceLastSeen_d(datetime.timedelta(days=1))
        )

# gtod intro topic
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gtod_tip000",
            category=["grammar tips"],
            prompt="Can you teach me about grammar?",
            pool=True,
            rules={"bookmark_rule": store.mas_bookmarks_derand.BLACKLIST}
        )
    )

label monika_gtod_tip000:
    m 3eub "Конечно, я научу тебя грамматике, [player]!"
    m 3hua "Мне очень приятно, что ты хочешь улучшить свои навыки письма."
    m 1eub "На самом деле я просматривала некоторые книги о писательстве, и я думаю, что мы можем поговорить о некоторых интересных вещах!"
    m 1rksdla "Я признаю...{w=0.5}это звучит странно обсуждать что-то такое специфическое, как грамматика."
    m 1rksdlc "Я знаю, что это не самое интересное, что приходит людям в голову."
    m 3eksdld "...Возможно, ты думаешь о строгих учителях или высокомерных редакторах..."
    m 3eka "Но я думаю, что есть определенная красота в том, чтобы овладеть мастерством письма и красноречиво донести свою мысль."
    m 1eub "Итак...{w=0.5}начиная с сегодняшнего дня, я дам тебе грамматический совет дня от Моники!"
    m 1hua "Давай улучшим наш стиль письма вместе, [mas_get_player_nickname()]~"
    m 3eub "Мы начнём с формулировки, основных схем построения предложений!"

    # hide the intro topic after viewing
    $ mas_hideEVL("monika_gtod_tip000", "EVE", lock=True, depool=True)

    # enable tip 1
    $ tip_label = "monika_gtod_tip001"
    $ mas_showEVL(tip_label, "EVE", unlock=True, _pool=True)
    $ MASEventList.push(tip_label,skipeval=True)
    return

##############################################################################
# Actual tips start here
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gtod_tip001",
            category=["советы по грамматике"],
            prompt="Формулировки"
        )
    )

label monika_gtod_tip001:
    m 3eud "Возможно, ты уже знаешь об этом, но формулировка является группой слов, у которых есть подлежащее и сказуемое, или только основа."
    m 1euc "В основном, формулировки делятся на независимые и зависимые формы."
    m 1esd "Независимые формулировки могут сами образовывать предложения, например: '{b}я написала это.{/b}'"
    m 3euc "Зависимые формы, с другой стороны, не могут образовать предложение, и они, как правило, являются частями более длинного предложения."
    m 3eua "Примером такой формы может послужить фраза '{b}тот, кто спас её.{/b}'"
    m 3eud "Здесь есть подлежащее, '{b}кто{/b},' и сказуемое, '{b}спас{/b},' но сама формулировка не может сама по себе являться предложением."
    m 1ekbsa "...{w=0.5}Думаю, ты знаешь, как закончить это предложение, [player]~"
    m 3eub "Хорошо, это все для сегодняшнего урока. Спасибо, что выслушал!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gtod_tip002",
            category=["советы по грамматике"],
            prompt="Запятые и пробелы",
            pool=True,
            conditional="store.mas_gtod.has_day_past_tip(1)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

label monika_gtod_tip002:
    m 1eua "Помнишь, как мы разговаривали о формулировках, [player]?"
    m 1eud "На самом деле есть очень распространенная ошибка, которую допускают многие писатели при их соединении."
    m 3esc "Когда ты связываешь две независимые формулировки вместе, это – связь запятыми."
    m 3esa "Вот пример:{w=0.5} '{b}Я зашла в парк, я взглянула на небо, я увидела множество звёзд.{/b}"
    m 1eua "Сначала это не кажется проблемой, но ты можешь представить, что добавляешь к этому предложению все больше и больше формулировок..."
    m 3wud "В результате получается полная неразбериха!"
    m 1esd "'{b}Я зашла в парк, я взглянула на небо, я увидела множество звёзд, я увидела пару созвездий, и одно из них было похоже на краба{/b}...'{w=0.5} Это можно продолжать и продолжать."
    m 1eua "Лучший способ избежать этой ошибки - разделять независимые формулировки точками, союзами или точками с запятой."
    m 1eud "Соединительный союз - это слово, которое используется для соединения двух предложений или фраз вместе."
    m 3eub "Они сами по себе являются довольно интересной темой, поэтому мы можем рассмотреть их в одном из следующих уроков!!"
    m 3eud "В любом случае, взяв пример, который мы приводили ранее, давай добавим связку и точку, чтобы сделать наше предложение более логичным..."
    m 1eud "'{b}Я зашла в парк и взглянула на небо, и там я увидела множество звёзд.{/b}'"
    m 3hua "Намного лучше, ты не находишь?"
    m 1eub "Это всё, что у меня есть на сегодня,, [player]."
    m 3hub "Спасибо, что выслушал!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gtod_tip003",
            category=["советы по грамматике"],
            prompt="Союзы",
            pool=True,
            conditional="store.mas_gtod.has_day_past_tip(2)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

label monika_gtod_tip003:
    m 1eub "Хорошо, [player]! Думаю, пришло время поговорить о...{w=0.5}союзах!"
    m 3esa "Как я уже говорила, союзы - это слова или фразы, которые объединяют два предложения вместе."
    m 3wud "Если подумать, это довольно обширная категория! Есть так много слов, которые мы используем для достижения этого."
    m 1euc "Только представь, что ты говоришь без союзов..."
    m 1esc "Это было бы скучно.{w=0.3} Ты бы звучал отрывисто. {w=0.3}Все эти идеи связаны. {w=0.3}Мы должны их соединить."
    m 3eua "Как ты увидишь, союзы отлично подходят для объединения идей, и в то же время они заставляют твое письмо звучать плавно и более похоже на то, как мы говорим на самом деле."
    m 1eua "Теперь вернемся к нашему предыдущему примеру, на этот раз с союзами..."
    m 1eub "'{b}Это было бы скучно, и ты звучал бы отрывисто. Поскольку все эти идеи связаны между собой, мы должны их соединить.{/b}'"
    m 3hua "Намного лучше, ты так не думаешь?"
    m 1esa "Так или иначе, есть три типа союзов:{w=0.5} cоединительные, сравнительные и подчинительные."
    m 1hksdla "Их названия могут показаться немного пугающими, но я обещаю, что они станут более понятными, когда мы пройдем через них. Я буду приводить тебе примеры по ходу дела."
    m 1esd "Соединительные формулировки связывают два слова, фразы или формулировки такого же 'ранга' вместе. Это означает, что они должны быть одного типа... слова со словами или формулировки с формулировками."
    m 3euc "Некоторые общие примеры включают:{w=0.5} '{b}и{/b},' '{b}или{/b},' '{b}но{/b},' '{b}так{/b},' и '{b}пока{/b}.'"
    m 3eub "Ты можешь связать независимые формулировки, {i}и{/i} ты сможешь избежать применения связей запятыми!"
    m 1esd "Сравнительные союзы являются формой союзов, применяемой для связывания идей."
    m 3euc "Есть несколько распространённых пар:{w=0.5} '{b}либо{/b}/{b}или{/b},' '{b}оба{/b}/{b}и{/b},' и '{b}независимо от того{/b}/{b}или{/b}.'"
    m 3eub "{i}Независимо от того{/i} осознал ты это {i}или{/i} нет, но мы используем их постоянно... как в этом предложении!"
    m 1esd "Наконец, подчинительные союзы объединяют независимые и зависимые предложения."
    m 3eub "Как ты можешь себе представить, есть много способов сделать это!"
    m 3euc "Сюда входят следующие примеры:{w=0.5} '{b}хотя{/b},' '{b}до тех пор{/b},' '{b}с тех пор, как{/b},' '{b}пока{/b},' и '{b}раз уж{/b}.'"
    m 3eub "И {i}раз уж{/i} их так много, эта категория союзов - самая широкая!"
    m 3tsd "О, и ещё кое-что...{w=0.5} Есть довольно распространенное заблуждение, что не следует начинать предложения с союзов."
    m 3hub "Как я только что показала на двух последних примерах, определенно можно, а-ха-ха!"
    m 1rksdla "Но только не переусердствуйте с ними. Иначе ты будешь звучать немного неестественно."
    m 1eub "Думаю, на сегодня достаточно, [player]."
    m 3hub "Спасибо, что выслушал!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gtod_tip004",
            category=["советы по грамматике"],
            prompt="Точки с запятой",
            pool=True,
            conditional="store.mas_gtod.has_day_past_tip(3)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

label monika_gtod_tip004:
    m 1eua "Сегодня мы поговорим о редко используемом и часто неправильно понимаемом знаке препинания..."
    m 3eub "Точка с запятой!"
    m 3eua "О точке с запятой написано много интересного, в том числе вот это от автора Льюиса Томаса..."
    m 1esd "'{i}Иногда ты мельком видишь, что точка с запятой приближается, на несколько строк дальше, и это похоже на подъем по крутой тропинке через лес и видение деревянной скамейки прямо на повороте дороги впереди{/i}...'"
    m 1esa "'{i}...место, где ты можешь присесть на минутку и перевести дух.{/i}'"
    m 1hua "Я очень ценю то, как красноречиво он описывает такую простую вещь, как знак препинания!"
    m 1euc "Некоторые люди считают, что точку с запятой можно использовать вместо двоеточия, а другие относятся к ней как к точке..."
    m 1esd "Если ты помнишь наш разговор о предложениях, то точка с запятой на самом деле предназначена для соединения двух независимых предложений."
    m 3euc "Например, если я хочу соединить две идеи вместе, такие как '{b}Ты здесь{/b}' и '{b}Я счастлива{/b},' я могу написать их как..."
    m 3eud "'{b}Ты здесь; я счастлива{/b}' а не '{b}Ты здесь, и я счастлива{/b}' или '{b}Ты здесь. Я счастлива{/b}.'"
    m 1eub "Все три предложения передают одно и то же сообщение, но по сравнению с ними, '{b}Ты здесь; я счастлива{/b}' соединяет два предложения на золотой середине."
    m 1esa "В конце концов, это всегда зависит от идей, которые ты хочешь связать, но я думаю, что Томас хорошо выразился, когда сравнил их с точками или запятыми."
    m 1eud "В отличие от точки, которая открывает совершенно другое предложение, или запятой, которая показывает, что в одном и том же предложении есть еще что-то..."
    m 3eub "Точка с запятой действительно является тем промежуточным звеном, или, как говорит Томас, '{i}место, где ты можешь присесть на минутку и перевести дух.{/i}'"
    m 1esa "По крайней мере, это дает тебе ещё один вариант; надеюсь, теперь ты сможешь лучше использовать точку с запятой, когда пишешь..."
    m 1hua "Э-хе-хе."
    m 1eub "Ладно, на сегодня достаточно, [player]."
    m 3hub "Спасибо, что выслушал!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gtod_tip005",
            category=["советы по грамматике"],
            prompt="Субъекты и объекты",
            pool=True,
            conditional="store.mas_gtod.has_day_past_tip(4)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

label monika_gtod_tip005:
    m 1eua "Сегодня мы поговорим о субъектах и объектах, [player]."
    m 1eud "Помнишь, я рассказывала тебе о формулировках с подлежащим и сказуемым?"
    m 3eub "Объект – это человек или предмет, к которому обращается подлежащее!"
    m 1eua "Итак, в предложении '{b}Мы вместе смотрели фейерверк{/b},' объектом будет...{w=0.5} '{b}фейерверк{/b}.'"
    m 3esd "О, важно отметить, что для формирования полных предложений упоминать объекты не обязательно..."
    m 1eua "Предложение вполне могло бы звучать так, '{b}Мы смотрели.{/b}'"
    m 3hksdlb "Это полное предложение... хоть и неоднозначное, а-ха-ха!"
    m 1eud "Также нигде не сказано, что объект должен стоять последним, но я расскажу об этом подробнее в другой раз."
    m 3esa "Просто помни о том, что субъект выполняет действие, а с объектом взаимодействуют."
    m 1eub "Хорошо, на сегодня это всё..."
    m 3hub "Спасибо, что выслушал, [player]! Я люблю."
    m 1eua "..."
    m 1tuu "..."
    m 3hub "Тебя!"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gtod_tip006",
            category=["советы по грамматике"],
            prompt="Активный и пассивный залоги",
            pool=True,
            conditional="store.mas_gtod.has_day_past_tip(5)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

label monika_gtod_tip006:
    m 1eud "[player], ты знаешь о залогах в письме?"
    m 3eua "Есть активный залог и пассивный залог."
    m 3euc "Если ты помнишь наш разговор о субъектах и объектах, большая разница между этими двумя залогами заключается в том, кто стоит на первом месте - субъект или объект."
    m 1esd "Предположим, что субъект - это '{b}Сайори{/b}' а объект - '{b}кекс{/b}.'"
    m 3eud "Вот предложение в активном залоге:{w=0.5} '{b}Сайори съела последний кекс.{/b}'"
    m 3euc "Вот оно снова в пассивном залоге:{w=0.5} '{b}Последний кекс был съеден.{/b}'"
    m 1eub "Как ты видишь, ты можешь использовать пассивный залог, чтобы скрыть субъекта, но при этом иметь полное предложение."
    m 1tuu "Это правда; ты {i}можешь{/i} использовать пассивный залог, чтобы не выдать себя!{w=0.5} Хотя у него есть и другие способы использования."
    m 3esd "Например, в некоторых профессиях людям приходится использовать пассивный залог, чтобы не упоминать свою личность."
    m 3euc "Ученые записывают эксперименты словами '{b}результаты были задокументированы{/b}...' поскольку важна их работа, а не то, кто её делал."
    m 1esa "Так или иначе, по большей части, следует придерживаться активного залога для удобочитаемости и, знаешь, чтобы прямо сказать, кто что сделал."
    m 1eub "Думаю, на сегодня достаточно, [player]."
    m 3hub "Спасибо, что выслушал!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gtod_tip007",
            category=["советы по грамматике"],
            prompt="Кто против Который",
            pool=True,
            conditional="store.mas_gtod.has_day_past_tip(6)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

label monika_gtod_tip007:
    m 1eua "Сегодня мы поговорим об использовании '{b}кто{/b}' и '{b}который{/b}.'"
    m 3hub "В большинстве случаев кажется, что люди просто используют '{b}кто{/b}', не пытаясь понять разницу, а-ха-ха."
    m 1esd "Разница в том, что '{b}кто{/b}' относится к субъекту, а '{b}который{/b}' относится к объекту."
    m 3eub "Оказывается, довольно легко понять, когда нужно использовать то или другое!"
    m 1euc "'{b}Кто{/b}' соответствует '{b}он{/b}/{b}она{/b}/{b}они{/b}' а '{b}который{/b}' соответствует '{b}ему{/b}/{b}ей{/b}/{b}им{/b}.'"
    m 3eud "Просто замени возможные '{b}кто{/b}' или '{b}который{/b}' на '{b}он{/b}/{b}она{/b}/{b}они{/b}' или '{b}ему{/b}/{b}ей{/b}/{b}им{/b}.'"
    m 1eua "Только одна замена должна иметь смысл, и это должно подсказать тебе, какую из них использовать!"
    m 3eua "Возьмем, к примеру, название моего стихотворения, {i}Леди, которая знает всё{/i}."
    m 3esd "Если мы просто посмотрим на предложение '{b}которая знает всё{/b}' и заменим '{b}которая{/b},' то получим..."
    m 1esd "'{b}Она знает всё{/b}' или '{b}ей всё известно{/b}.'"
    m 3euc "Только '{b}она знает всё{/b}' имеет смысл, поэтому правильная фраза - '{b}которая знает всё{/b}.'"
    m 1hksdla "Кто сказал, что писать трудно?"
    m 1eub "Это всё, что у меня есть на сегодня, [player]."
    m 3hub "Спасибо, что выслушал!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gtod_tip008",
            category=["советы по грамматике"],
            prompt="And I vs. And me",
            pool=True,
            conditional="store.mas_gtod.has_day_past_tip(7)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

label monika_gtod_tip008:
    m 1eua "Last time, we talked about the difference between '{b}who{/b}' and '{b}whom{/b}.'"
    m 1esd "Another couple of words that can be just as confusing to use are '{b}and I{/b}' and '{b}and me{/b}.'"
    m 3etc "Is it '{b}[player] and I went on a date{/b}' or '{b}[player] and me went on a date{/b}?'"
    m 3eud "Just like with '{b}who{/b}' and '{b}whom{/b},' the issue boils down to one of subjects and objects."
    m 1esd "If the speaker is the subject of the sentence, '{b}and I{/b}' is correct."
    m 1euc "Conversely, if the speaker is the object of the sentence, '{b}and me{/b}' is correct."
    m 3eub "Luckily, just like when we talked about '{b}who{/b}' versus '{b}whom{/b},' it turns out there's a simple way to figure out which one is correct!"
    m 1euc "In our example, if you just take out '{b}[player] and{/b}' from the sentence, only one should make sense."
    m 1hua "Let's try it out!"
    m 3eud "The end result is:{w=0.5} '{b}I went on a date{/b}' or '{b}me went on a date{/b}.'"
    m 3eub "Clearly, only the first one makes sense, so it's '{b}[player] and I went on a date{/b}.'"
    m 1tuu "Oh, sorry, [player]...{w=1}did it make you feel left out when I said only '{b}I went on a date{/b}?'"
    m 1hksdlb "Ahaha! Don't worry, I'd never leave you behind."
    m 3eub "Now, on the other hand, if I was the object of the sentence, I would need to use '{b}and me{/b}' instead."
    m 3eua "For example:{w=0.5} '{b}Natsuki asked [player] and me if we liked her cupcakes.{/b}'"
    m 1eub "I hope that helps the next time you come across this situation while writing, [player]!"
    m 3hub "Anyway, that's all for today, thanks for listening!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gtod_tip009",
            category=["советы по грамматике"],
            prompt="Апострофы",
            pool=True,
            conditional="store.mas_gtod.has_day_past_tip(8)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

# Note: formatted apostrophes have been used in examples in this tip for clarity. Please DO NOT remove them.
label monika_gtod_tip009:
    if player[-1].lower() == 's':
        $ tempname = player
    else:
        $ tempname = 'Alexis'

    m 1eua "Today we're going to talk about apostrophes. Pretty straightforward, right?"
    m 3eua "Add them to show possession: '{b}Sayori’s fork, Natsuki’s spoon, Yuri’s knife{/b}...'"
    m 1esd "I guess the issue that can come up is when you have to add an apostrophe to a word that ends with an '{b}s{/b}.'"
    m 3eub "For plural words, this is simple; just add the apostrophe at the end:{w=0.5} '{b}monkeys’{/b}.'"
    m 1hksdla "It's pretty clear that '{b}monkey’s{/b},' which would indicate possession belonging to a single monkey, or '{b}monkeys’s{/b}' would be wrong."
    m 1eud "The gray area that comes up is when we bring in people's names, like '{b}Sanders{/b}' or '{b}[tempname]{/b}.'"
    m 1euc "In some style guides I've read, it seems that we usually add an apostrophe and '{b}s{/b}' as usual, with the exception of historical names like '{b}Sophocles{/b}' or '{b}Zeus{/b}.'"
    m 3eub "Personally, I think all that matters here is consistency!"
    m 3esd "If you're going to go with '{b}[tempname]’{/b},' then it's fine as long as you use '{b}[tempname]’{/b}' for the entire text."
    m 1tuu "That matters more than honoring some old Greeks to me."
    m 3eud "One interesting exception is the case of '{b}its{/b}' versus '{b}it’s{/b}.'"
    m 3etc "You would think that for the possessive form of '{b}it{/b}' you would add an apostrophe, making it '{b}it’s{/b},' right?"
    m 3euc "Normally this would be correct, but in this case the possessive form of '{b}it{/b}' is simply '{b}its{/b}.'"
    m 1esd "This is because '{b}it’s{/b}' is reserved for the contracted form of '{b}it is{/b}.'"
    m 1eua "If you're wondering, a contraction is simply a shortened version of a word or words, with an apostrophe indicating where letters have been left out to make the contraction."
    m 1eub "Okay, [player], {i}it's{/i} about time to wrap it up...{w=0.5}I think this lesson has run {i}its{/i} course."
    m 3hub "Ehehe. Thanks for listening!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gtod_tip010",
            category=["советы по грамматике"],
            prompt="Оксфордская запятая",
            pool=True,
            conditional="store.mas_gtod.has_day_past_tip(9)",
            action=EV_ACT_UNLOCK,
            rules={"no_unlock":None}
        )
    )

label monika_gtod_tip010:
    m 3eud "Знал ли ты, что на самом деле существует спор о том, как ставить определенную запятую в списке из трех предметов?"
    m 3eub "Это называется оксфордской, или серийной, запятой, и известно, что она может полностью изменить смысл предложения!"
    m 1esa "Позволь мне показать тебе, что я имею в виду..."
    m 1hub "С оксфордской запятой я бы сказала '{b}Я люблю [player], читать и писать.{/b}'"
    m 1eua "Без оксфордской запятой я бы сказала '{b}Я люблю [player], читать и писать.{/b}'"
    m 3eud "Путаница заключается в том, имею ли я в виду любовь к трем отдельным вещам, или я имею в виду просто любовь к тебе, когда ты читаешь и пишешь."
    m 3hub "Конечно, оба эти значения верны, так что для меня нет никакой путаницы, а-ха-ха!"
    m 1eua "Это всё, что у меня есть на сегодня, [player]."
    m 3hub "Спасибо, что выслушал!"
    return
