# Storyboard: animowane video CV Dominiki Romanow

Styl: oryginalny, plaski explainer video z cieplymi kolorami, prostymi ikonami, lagodnymi przejsciami i napisami ekranowymi. Film jest inspirowany formatem lekkiego animowanego CV, ale nie kopiuje konkretnego materialu.

| Czas | Scena | Wizual | Tekst lektora / napis |
| --- | --- | --- | --- |
| 00:00-00:10 | Intro | Portret, pinezka mapy, zarys miasta | Cześć, jestem Dominika Romanow. Pochodzę z Olsztyna i szukam pierwszej pracy w HR. |
| 00:10-00:19 | Bliźniaczka | Dwie postacie, dymki rozmowy, kawałek ciasta | Dorastałam z siostrą bliźniaczką, więc od małego ćwiczyłam negocjacje, współpracę i dzielenie się wszystkim. |
| 00:19-00:29 | Restauracja | Taca, talerz, zegar, dynamiczne kreski | Pierwszą szkołą tempa była restauracja: kontakt z ludźmi, organizacja i spokojne reagowanie w ruchu. |
| 00:29-00:41 | Gdańsk i prace z klientami | Miasto, uczelnia, piekarnia, event, sklep | W Gdańsku zaczęłam psychologię w biznesie na WSB Merito i pracowałam z klientami w piekarni, na eventach i w Żabce. |
| 00:41-00:51 | Wyróżnienie i HR | Dyplom, medal, litery HR | Dobra średnia przyniosła wyróżnienie Rektora. Po licencjacie wybrałam HR i magisterkę z zarządzania zasobami ludzkimi. |
| 00:51-01:03 | ESN Gdańsk | Lejek rekrutacyjny, karty kandydatów, autobus | W ESN Gdańsk działałam w sekcji HR: prowadziłam rekrutacje i współorganizowałam wyjazd szkoleniowo-integracyjny. |
| 01:03-01:12 | Erasmus Porto | Samolot, trasa, ocean, słońce | Teraz przygotowuję się do Erasmusa w Porto, żeby rozwijać się w międzynarodowym środowisku. |
| 01:12-01:21 | Szydełkowanie | Motek włóczki, nitka przechodząca w sieć połączeń | Po godzinach szydełkuję. Lubię patrzeć, jak z jednej nitki powstaje coś konkretnego - trochę jak w HR. |
| 01:21-01:30 | Zakończenie | Portret, checklista kompetencji, badge HR | Jestem otwarta, dobrze zorganizowana i gotowa na nowe wyzwania. Chętnie dołączę do międzynarodowego zespołu HR. |

## Użycie

1. Wygeneruj wideo:
   ```bash
   python3 video_cv/generate_animated_cv.py
   ```
2. Jeśli masz nagrany lektor, dołącz go podczas renderu:
   ```bash
   python3 video_cv/generate_animated_cv.py --voiceover sciezka/do/lektora.wav
   ```
3. Wynik zapisze się w `video_cv/output/dominika_romanow_video_cv.mp4`, a napisy w `video_cv/output/dominika_romanow_video_cv.srt`.
