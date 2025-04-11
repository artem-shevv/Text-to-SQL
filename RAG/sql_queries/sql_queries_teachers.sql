-- Вся информация обо мне как преподавателе?
WITH teacher_data AS (
    SELECT 
        T.TE_NO AS "Мой номер",
        T.FULL_NAME AS "Моё ФИО",
        -- Контактные телефоны
        (
            SELECT STRING_AGG(PL.PHONE_NUMBER, ', ')
            FROM PHONE_LIST PL
            WHERE PL.TE_NO = T.TE_NO
        ) AS "Мои телефоны",
        
        -- Курируемые группы
        (
            SELECT STRING_AGG(G.ID_NO::TEXT, ', ')
            FROM GROUPS G
            WHERE G.CURATOR_NO = T.TE_NO
        ) AS "Номера курируемых групп",
        
        -- Преподаваемые предметы с кодами
        (
            SELECT STRING_AGG(S.SU_NO::TEXT || ' - ' || S.SUBJECT, '; ')
            FROM SUBJECTS S
            WHERE S.TE_NO = T.TE_NO
        ) AS "Мои предметы",
        
        -- Курсы, где преподаю
        (
            SELECT STRING_AGG(DISTINCT C.CR_NO::TEXT, ', ')
            FROM COURSE C
            JOIN SUBJECTS S ON C.LIST_SU_NO::bigint[] @> ARRAY[S.SU_NO]::bigint[]
            WHERE S.TE_NO = T.TE_NO
        ) AS "Мои курсы",
        
        -- Количество студентов (исправленный подсчет)
        (
            SELECT COUNT(DISTINCT ST.ST_NO)
            FROM STUDENTS ST
            JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
            JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
            JOIN SUBJECTS S ON C.LIST_SU_NO::bigint[] @> ARRAY[S.SU_NO]::bigint[]
            WHERE S.TE_NO = T.TE_NO
        ) AS "Количество моих студентов"
    FROM TEACHERS T
    WHERE T.TE_NO = '08-731-2673'
)

SELECT * FROM teacher_data;





--Сколько студентов я обучаю?
SELECT COUNT(DISTINCT ST.ST_NO) AS "Количество студентов"
    FROM STUDENTS ST
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
    JOIN SUBJECTS S ON C.LIST_SU_NO::bigint[] @> ARRAY[S.SU_NO]::bigint[]
    WHERE S.TE_NO = '80-014-3241';




--Кто из студентов изучает мой предмет "Нейронные сети"?
WITH 
-- Находим номер предмета "Нейронные сети"
subject_info AS (
    SELECT SU_NO 
    FROM SUBJECTS 
    WHERE SUBJECT = 'Нейронные сети'
    LIMIT 1
),

-- Находим курсы, где изучается этот предмет
courses_with_subject AS (
    SELECT C.ID_NO
    FROM COURSE C, subject_info si
    WHERE si.SU_NO = ANY(C.LIST_SU_NO::bigint[])
),

-- Находим группы, изучающие эти курсы
groups_with_subject AS (
    SELECT G.ID_NO
    FROM GROUPS G
    JOIN courses_with_subject cws ON G.ID_NO_CR = cws.ID_NO
),

-- Получаем студентов этих групп
students_list AS (
    SELECT DISTINCT ST.ST_NO, ST.SURNAME, ST.NAME
    FROM STUDENTS ST
    JOIN groups_with_subject gws ON ST.ID_NO_GR = gws.ID_NO
)

-- Выводим с нумерацией и общим количеством
SELECT 
    ROW_NUMBER() OVER (ORDER BY SURNAME, NAME) AS "№",
    ST_NO AS "Номер студента",
    SURNAME AS "Фамилия",
    NAME AS "Имя"
FROM students_list
ORDER BY SURNAME, NAME;






--Какие оценки получили студенты по моему предмету/предметам?(нужно вывести id студента и его оценку по всем предметам, которые ведёт преподаватель с своим te_no)





--В каких группах учатся студенты, которым я читаю предметы?(нужно вывести id групп)


--Какие у меня есть контакты студентов-старост?(выводится список номеров старост, где преподаватель является кураторм)


--Какие предметы я веду?


--Какие курсы содержат мои предметы?


--Кто из студентов не сдал мой предмет?(получил 2 в случае экзамена или "Не сдал" в случае зачёта)


--Сколько студентов получили 5 по моему предмету?


--Кто является куратором конкретной группы?


--В каких группах я являюсь куратором?


--Как записан мой телефон, указанный в системе?


--Кто из студентов сдавал экзамен по моему предмету и на какую оценку?


--Какие предметы читает/ведёт преподаватель N?


--Номера старост в подшефных группах?