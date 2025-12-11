# Komunitní kalendář 

# 1. Úvod
Community Calendar je webová aplikace, kde si uživatelé můžou sdílet, spravovat a kombinovat různé kalendáře s akcemi.  
Cílem je mít jeden hlavní komunitní kalendář a zároveň umožnit každému uživateli poskládat si svůj osobní kalendář z různých zdrojů (včetně ICS importů).


# 2. Funkční požadavky

# 2.1 Co má aplikace umět
- Registrace a přihlášení uživatelů  
- Zobrazení hlavního komunitního kalendáře  
- Organizátoři/admini: tvorba, úprava a mazání akcí  
- Uživatel: přihlášení/odhlášení z akcí  
- Import externích kalendářů:
  - ICS URL
  - nahrání ICS souboru  
- Osobní kalendář uživatele:
  - akce, kam se přihlásil  
  - importované ICS události   
- Export osobního kalendáře jako ICS  
- Správa uživatelských rolí a oprávnění  
- Přehledné a jednoduché UI pro práci s kalendáři  

#  3. Funkční specifikace

## 3.1 Role a oprávnění

Admin
- Má plný přístup k aplikaci  
- Může spravovat všechny akce  
- Může upravovat uživatele a role  
- Může vidět osobní kalendáře všech uživatelů  

Organizer
- Může vytvářet a upravovat vlastní akce  
- Vidí seznam účastníků svých akcí  
- Může měnit detaily svých událostí  

User
- Vidí komunitní kalendář  
- Může se přihlásit/odhlásit z akcí  
- Může importovat ICS kalendáře  
- Má svůj osobní kalendář  

# 4. Konceptuální datový model 

User
- id  
- email  
- password_hash  
- role  

Event
- id  
- title  
- description  
- location  
- start_datetime  
- end_datetime  
- organizer_id - User.id  

EventParticipant
- user_id - User.id  
- event_id - Event.id  

PersonalEvent
- id  
- User.id  
- title  
- start_datetime  
- end_datetime  

ImportedCalendar
- id  
- user_id - User.id  
- source_url  
- last_sync  
- raw_ics_data  

Vztahy:
- User 1:N Event  
- User N:M Event (přes EventParticipant)  
- User 1:N PersonalEvent  
- User 1:N ImportedCalendar  


# 5. Uživatelské rozhraní

5.1 Hlavní části UI

Dashboard
- Přehled nadcházejících akcí  
- Rychlé akce (Join event, Import kalendáře, Vytvořit událost)

Komunitní kalendář
- Přepínání měsíc/týden/den  
- Detail akce v popupu  
- Tlačítko “Přihlásit se na akci”

Osobní kalendář
- Spojené akce uživatele  
- Filtry: Importované / Přihlášené / Vlastní  
- Export ICS

Nastavení
- Úprava profilu  
- Správa importovaných kalendářů  
- Přidání ICS URL / nahrání ICS souboru  

# 6. Technická specifikace

6.1 Logický datový model

users
| column         | type      | notes |
|----------------|-----------|-------|
| id             | PK int    |       |
| email          | varchar   | unique |
| password_hash  | varchar   |       |
| role           | enum      | admin/organizer/user |

events
| column         | type      |
|----------------|-----------|
| id             | PK int    |
| title          | varchar   |
| description    | text      |
| location       | varchar   |
| start_datetime | datetime  |
| end_datetime   | datetime  |
| organizer_id   | FK → users.id |

event_participants
| column   | type |
|----------|------|
| user_id  | FK   |
| event_id | FK   |

personal_events
| column         | type |
|----------------|------|
| id             | PK   |
| user_id        | FK   |
| title          | varchar |
| start_datetime | datetime |
| end_datetime   | datetime |

imported_calendars
| column      | type |
|-------------|------|
| id          | PK   |
| user_id     | FK   |
| source_url  | varchar |
| last_sync   | datetime |
| raw_ics_data | text |

# 7. Architektura aplikace

# Frontend
- React  
- FullCalendar  
- TailwindCSS  

# Backend
- Python FastAPI  
- API pro práci s uživateli, akcemi a kalendáři  
- Autentizace přes JWT  
- Parsování ICS (např. ical.js nebo Python ICS knihovna)  
- Export ICS

# Databáze
- PostgreSQL  
- SQLAlchemy (Python)

# 8. Backend – popis tříd

UserService
- registerUser()  
- loginUser()  
- updateRole()  
- getUserById()  

EventService
- createEvent()  
- updateEvent()  
- deleteEvent()  
- getEventById()  
- listEvents()  

ParticipantService
- joinEvent(userId, eventId)  
- leaveEvent(userId, eventId)  

CalendarImportService
- fetchICS(url)  
- parseICS(data)  
- saveImportedEvents()  
- scheduleSync()  

CalendarExportService
- generateICS(userId)  

# 9. Technologie

# Frontend
- React  
- FullCalendar  
- TailwindCSS  

# Backend
- FastAPI  
- JWT  
- ICS parser

# Databáze
- PostgreSQL  
- SQLAlchemy

# Ostatní
- Git + GitHub  
- Docker  
- REST API  


