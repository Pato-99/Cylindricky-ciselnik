# Cylindrický číselník

![Showcase](/media/showcase.gif)

Mechanický cylindrický číselník je obdoba takzvaných "flip-clock" s tím,
že místo "flipujících" dlaždiček se otáčejí cylindry (válce). Díky tomu je možné
otáčet číselníkem na obě strany a také je ho možné umístit v jakékoliv poloze,
protože ke změně čísel není potřeba gravitace tak jako u "flip-clock".


## Klíčové vlastnosti

- modularita
- jednoduché rozhraní
- asynchronní ovládání jednotlivých válců


## Ovládání/Rozhraní

Číselník lze ovládat pomocí jednoduchých příkazů přes UART nebo MQTT

| Příkaz              | Popis                                                                                     |
|---------------------|-------------------------------------------------------------------------------------------|
| `SHOW <int>`        | Zobrazí dané číslo. Pokud je počet číslic větší než počet cylindrů, tak se ořízne zprava. |
| `SHOWF <float> <n>` | Zobrazí float na n desetinných míst. Případně se číslo ořízne zprava.                     |
| `INFO`              | Vypíše info jaké číslo je právě zobrazováno a stavy motorů.                               |
| `CONFIGURE`         | Spustí konfigurační mód.                                                                  |

### Konfigurační mód

Pomocí posílání číslovek (`1, 2, 3, 4, 5, 6, ...`) se po jednotlivých krocích nastaví motory tak,
aby displej ukazoval samé nuly. Potom posláním `s` nastavení uložíme.

Nastavení je poté uloženo ve flash paměti zařízení a tak zůstává zachováno
i po rebootu.

## Implementace SW

K implementaci SW byl použit programovací jazyk MicroPython.

Program se skládá ze 2 hlavních částí:

1. Zpracování vstupu
2. Driver displeje/motorů

V samotné implementaci driveru byly použity 3 úrovně abstrakce.

1. Driver samotného unipolárního krokového motoru
2. Driver jednotlivých cylindrů (motor, převod, logika zobrazování číslic)
3. Driver displeje jako celku (skládá se z cylindrů)


### Asynchronní ovládání

Ovládání jednotlivých motorů je řešeno asynchronně pomocí knihovny `uasyncio`.

Asynchronní programování se hodí použít tam, kde jsou procedury takzvaně "I/O bound.
To znamená, že většinu času běhu procedury zabírá čekání například na vstup,
na navázání spojení atd. V našem případě je to čekání mezi jednotlivými kroky
krokového motoru. Myšlenkou je využití tohoto času pro něco užitečnějšího.
Díky tomu můžeme dosáhnout určité míry paralelismu za použití jen jednoho
vlákna.

Základem jsou klíčová slova `async` a `await`.

Připsáním klíčového slova `async` před deklaraci funkce říkáme, že se jedná
o takzvanou **courutine** a že se o její běh bude starat uasyncio. Coroutines 
je možné volat z jiných coroutines za použítí klíčového slova `await` nebo
předáním jako parametr funkcím z uasyncio knihovny (run(), gather()...).


**Asynchronní implementace otočení motoru o určitý počet kroků:**
```python
async def turn_steps(self, steps):
    reverse = False
    if steps < 0:
        reverse = True
        steps = -steps
    for _ in range(steps):
        self.step(reverse)
        await asyncio.sleep_ms(self.delay)
```

**Otáčení 3 cylindry naráz:**
```python
async def show(self, number):
    await asyncio.gather(
        self.digit2.show((number // 100) % 10),
        self.digit1.show((number // 10) % 10),
        self.digit0.show(number % 10)
    )
```

Zde funkce `asyncio.gather()` spustí otáčení všech 3 cylindrů naráz
a skončí až se dotočí poslední.


### MQTT

Původně bylo v plánu i ovládání přes MQTT přímo pomocí desky s WiFi čipem 
RPi Pico W, ale po testování se ukázalo, že tato metoda není úplně spolehlivá.
Vyskytovaly se časté výpadky spojení. Proto jsem napsal script, který běží na PC
a přes UART přeposílá příkazy z MQTT do připojeného RPi Pico.


## Konsktrukce

![Disassembled](/media/disassembled.jpg)

Při designu číselníku byl kladen důraz na to, aby byla konsktrukce co nejvíce modulární
a také aby se použily pouze běžně dostupné součástky. Díky tomu lze snadno postavit
číselník s libovolným počtem cylindrů.


### Použité součástky:

- RPi Pico
- tranzistorové pole ULN2004
- elektrolytické kondenzátory 44 uF
- krokové motory z AliExpressu řízené unipolárně

- šroub s válcovou hlavou s vnitřním šestihranem M3
- matice M3
- ložiska 608
- tyč D=8mm
- neodymové magnety

- 3D tištěné díly


## TODO

* implementace pro jednoduché zapojení libovolného počtu motorů
  pomocí **tuple unpacking**
* built-in mqtt
* upravit konsktrukci pro motory 28BYJ-48


## Užitečné odkazy

* [MicroPython](https://micropython.org/)
* [uasyncio](https://docs.micropython.org/en/latest/library/uasyncio.html)
