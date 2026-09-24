Звід по мануальному тесту прошивки Bluedroid_GATT_Server_merged.bin

1. 
Що робили
Scan – у nRF Connect знайти пристрій SENTRY-BLE, зафіксувати RSSI.

Що очікували
FR-A1. Пристрій рекламується під іменем SENTRY-BLE, доступний для підключення.

Що отимали(доказ)
Пристрій рекламується очікувано, як SENTRY-BLE. RSSI -50dBm. Доступний до підключення
![alt text](images/evid_1.png)

2. 
Що робили
Connect + discovery – підключитись; переконатись, що є сервіси 0x180D (Heart Rate) і 0x1815 (Automation IO), а в 0x1815 – дві характеристики (LED і RELAY, UUID у PRD). У UART-лозі - Connected, ... remote <MAC>.

Що очікували
FR-A3. Підключення/відключення логуються в UART: Connected, conn_id ..., remote <MAC> / Disconnected ....

FR-G1. Heart Rate Service 0x180D з характеристикою 0x2A37 (read + indicate). Пульс оновлюється щосекунди, нормальний діапазон 60-80 bpm.

FR-G3. Automation IO Service 0x1815 з двома характеристиками (128-бітні UUID):
 LED 00001525-1212-efde-1523-785feabcd123 (read/write)
 RELAY 00001526-1212-efde-1523-785feabcd123 (read/write)

Що отримали(доказ)
 - В в UART connect та disconnect логуються як очікувано
```
I (1241797) GATTS_DEMO: Connected, conn_id 0, remote 6d:17:64:b7:69:bf
I (1241797) GATTS_DEMO: Connected, conn_id 0, remote 6d:17:64:b7:69:bf
I (1241897) GATTS_DEMO: Packet length update, status 0, rx 27, tx 251
I (1242217) GATTS_DEMO: Connection params update, status 0, conn_int 24, latency 0, timeout 400
I (1242437) GATTS_DEMO: Connection params update, status 0, conn_int 6, latency 0, timeout 500
```
```
W (1240327) BT_HCI: hcif disc complete: hdl 0x1, rsn 0x13 dev_find 1
I (1240327) GATTS_DEMO: Disconnected, remote 6d:17:64:b7:69:bf, reason 0x13
I (1240327) GATTS_DEMO: Disconnected, remote 6d:17:64:b7:69:bf, reason 0x13
```
 - Пульс оновлюється щосекунди у межах 60-80
```
I (1232527) GATTS_DEMO: Attribute value set, status 0
I (1233527) GATTS_DEMO: Heart Rate updated to 60
I (1233527) GATTS_DEMO: Attribute value set, status 0
I (1234527) GATTS_DEMO: Heart Rate updated to 72
I (1234527) GATTS_DEMO: Attribute value set, status 0
I (1235527) GATTS_DEMO: Heart Rate updated to 76
I (1235527) GATTS_DEMO: Attribute value set, status 0
I (1236527) GATTS_DEMO: Heart Rate updated to 70
I (1236527) GATTS_DEMO: Attribute value set, status 0
I (1237527) GATTS_DEMO: Heart Rate updated to 77
I (1237527) GATTS_DEMO: Attribute value set, status 0
I (1238527) GATTS_DEMO: Heart Rate updated to 72
I (1238527) GATTS_DEMO: Attribute value set, status 0
I (1239527) GATTS_DEMO: Heart Rate updated to 61
```
 - Heart Rate Service 0x180D з характеристикою 0x2A37 (read + indicate), як очікувано
 - Automation IO Service 0x1815 з двома характеристиками **АЛЕ замість RELAY маємо unknown Characteristic**
 ![alt text](images/evid_2.png)

3. 
Що робили
Heart Rate – підписатись на індикації 0x2A37: значення оновлюються щосекунди, діапазон 60-80 bpm.

Що очікували
FR-G1. Heart Rate Service 0x180D з характеристикою 0x2A37 (read + indicate). **Пульс оновлюється щосекунди, нормальний діапазон 60-80 bpm.**

FR-G2. Підписка на indications через CCCD: після підписки клієнт отримує оновлення пульсу щосекунди.

Що отимали(доказ)
Клієнт отримує оновлення пульсу щосекунди у діапазонах 60-80(найкращим доказом було б відео але в рамках навчання та постановки завдання прикладаю скріншот)
![alt text](images/evid_3.png)

4. 
Що робили
HR spike – у UART-терміналі команда hr spike (або кнопка K1): у nRF Connect наступні значення ~190. Скрін з аномальним значенням.

Що очікували
FR-C3. hr spike (і кнопка K1) інжектить аномальний пульс ~190-199 bpm на 5 секунд - для перевірки реакції клієнта на позаштатні значення.

Що отимали(доказ)
Працює як учікувано
```
I (2542517) GATTS_DEMO: heart rate spike injected (5 ticks)

W (2542527) GATTS_DEMO: Heart Rate SPIKE injected: 190
I (2542527) GATTS_DEMO: Attribute value set, status 0
W (2543527) GATTS_DEMO: Heart Rate SPIKE injected: 192
I (2543527) GATTS_DEMO: Attribute value set, status 0
W (2544527) GATTS_DEMO: Heart Rate SPIKE injected: 191
I (2544527) GATTS_DEMO: Attribute value set, status 0
W (2545527) GATTS_DEMO: Heart Rate SPIKE injected: 195
I (2545527) GATTS_DEMO: Attribute value set, status 0
W (2546527) GATTS_DEMO: Heart Rate SPIKE injected: 198
I (2546527) GATTS_DEMO: Attribute value set, status 0
```
```
I (2639777) GATTS_DEMO: button 1 pressed (GPIO41)
I (2639777) GATTS_DEMO: [K1] heart rate spike (5 ticks)
W (2640527) GATTS_DEMO: Heart Rate SPIKE injected: 194
I (2640527) GATTS_DEMO: Attribute value set, status 0
W (2641527) GATTS_DEMO: Heart Rate SPIKE injected: 191
I (2641527) GATTS_DEMO: Attribute value set, status 0
W (2642527) GATTS_DEMO: Heart Rate SPIKE injected: 196
I (2642527) GATTS_DEMO: Attribute value set, status 0
W (2643527) GATTS_DEMO: Heart Rate SPIKE injected: 199
I (2643527) GATTS_DEMO: Attribute value set, status 0
W (2644527) GATTS_DEMO: Heart Rate SPIKE injected: 190
I (2644527) GATTS_DEMO: Attribute value set, status 0
```

5. 
Що робили
LED через BLE – write 01 у LED-характеристику: фізичний LED загорівся, у лозі LED ON!. Write 00 - згас, LED OFF!.

Що очікували
FR-G4. Write 0x01/0x00 у LED/RELAY вмикає/вимикає фізичний LED / реле (GPIO8) і пише в UART LED ON!/LED OFF! або RELAY ON!/RELAY OFF!

Що отимали(доказ)
Фізичний лед вмикається/вимикається у відповідності до вимог, логи співпадають з вимогами.
Щодо write 01/00 у LED-характеристику, фактично присутні значення ON/OFF що технічно відповідають вимогам, але фактично є неточністю яку бажано або змінити у вимогах або реалізувати у відповідності до вимог.
![alt text](images/evid_5.png)
```
I (3005377) GATTS_DEMO: Characteristic write, value len 1, value
I (3005377) GATTS_DEMO: 01
I (3005377) GATTS_DEMO: LED ON!
```
```
I (3104507) GATTS_DEMO: Characteristic write, value len 1, value
I (3104507) GATTS_DEMO: 00
I (3104507) GATTS_DEMO: LED OFF!
```

6. 
Що робили
RELAY через BLE – write 01/00 у RELAY-характеристику: клацання реле, у лозі RELAY ON!/RELAY OFF!.

Що очікували
FR-G4. Write 0x01/0x00 у LED/RELAY вмикає/вимикає фізичний LED / реле (GPIO8) і пише в UART LED ON!/LED OFF! або RELAY ON!/RELAY OFF!

Що отримали(доказ)
Write 01/00 викликає клацання реле у відповідності з вимогами. Логи також відповідають вимогам
```
I (4454137) GATTS_DEMO: Characteristic write, value len 1, value
I (4454137) GATTS_DEMO: 01
I (4454137) GATTS_DEMO: RELAY ON!
```
```
I (4466107) GATTS_DEMO: Characteristic write, value len 1, value
I (4466107) GATTS_DEMO: 00
I (4466107) GATTS_DEMO: RELAY OFF!
```

7. 
Що робили
Read після write – після write 01 read характеристики повертає 01 (і так само для 00).

Що очікували
FR-G5. Read LED/RELAY повертає актуальний стан (1 байт: 0 або 1), включно з випадком, коли стан змінили локально (кнопкою або CLI).

Що отримали(доказ)
Через nRF Connect for Mobile все рпацює у відповідності до вимог
![alt text](images/evid_7_1.png)

![alt text](images/evid_7_2.png)

8. 
Що робили
Конфлікт каналів керування – write 01 у LED по BLE, потім вимкнути LED іншим каналом (кнопка K2 або UART-команда led off), потім read по BLE: має повернутись 00 (PRD FR-G5).

Що очікували
FR-G5. Read LED/RELAY повертає актуальний стан (1 байт: 0 або 1), включно з випадком, коли стан змінили локально (кнопкою або CLI).

Що отримали(доказ)
Конфлікт каналів відсутній. Перевірені всі комбінації трьох каналів: BLE/CLI/фізичні кнопки
Для всих комбінацій скріни та логи займатимуть багато місця, тобу нижче логи та скріни після одного з кейсів
```
I (6139267) GATTS_DEMO: Characteristic write, value len 1, value
I (6139267) GATTS_DEMO: 01
I (6139267) GATTS_DEMO: LED ON!
I (6139527) GATTS_DEMO: Heart Rate updated to 76
I (6139527) GATTS_DEMO: Attribute value set, status 0
I (6140527) GATTS_DEMO: Heart Rate updated to 76
I (6140527) GATTS_DEMO: Attribute value set, status 0
I (6141527) GATTS_DEMO: Heart Rate updated to 73
I (6141527) GATTS_DEMO: Attribute value set, status 0
I (6142527) GATTS_DEMO: Heart Rate updated to 60
I (6142527) GATTS_DEMO: Attribute value set, status 0
I (6143527) GATTS_DEMO: Heart Rate updated to 67
I (6143527) GATTS_DEMO: Attribute value set, status 0
I (6144477) GATTS_DEMO: button 2 pressed (GPIO40)
I (6144477) GATTS_DEMO: [K2] LED toggle (local)
I (6144477) GATTS_DEMO: LED OFF!
```
![alt text](images/evid_8.png)

9. 
Що робили
Reconnect – розірвати з'єднання (з nRF Connect або UART-командою disconnect): у лозі Disconnected, пристрій знову видно у скані, повторне підключення працює.

Що очікували
FR-A2. Після розриву з'єднання реклама відновлюється автоматично (пристрій можна знайти знову без ребута).
FR-A3. Підключення/відключення логуються в UART: Connected, conn_id ..., remote <MAC> / Disconnected ....

Що отримали(доказ)
Все відповідає вимогам.
```
I (89527) GATTS_DEMO: Attribute value set, status 0
t

I (90207) GATTS_DEMO: dropping BLE connection
W (90207) BT_HCI: hci cmd send: disconnect: hdl 0x1, rsn:0x13


W (90227) BT_HCI: hcif disc complete: hdl 0x1, rsn 0x16 dev_find 1
I (90227) GATTS_DEMO: Disconnected, remote 78:83:b0:3d:29:ed, reason 0x16
I (90227) GATTS_DEMO: Disconnected, remote 78:83:b0:3d:29:ed, reason 0x16
I (90237) GATTS_DEMO: Advertising start successfully
```
```
I (347837) GATTS_DEMO: Connected, conn_id 0, remote 78:83:b0:3d:29:ed
I (347837) GATTS_DEMO: Connected, conn_id 0, remote 78:83:b0:3d:29:ed
I (347937) GATTS_DEMO: Packet length update, status 0, rx 27, tx 251
I (348237) GATTS_DEMO: Connection params update, status 0, conn_int 24, latency 0, timeout 400
I (348457) GATTS_DEMO: Connection params update, status 0, conn_int 6, latency 0, timeout 500
I (348527) GATTS_DEMO: Heart Rate updated to 60
```
![alt text](images/evod_9.png)
