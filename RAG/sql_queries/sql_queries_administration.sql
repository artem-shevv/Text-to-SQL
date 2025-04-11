-- Сколько всего студентов обучается?
SELECT COUNT(*) AS "Общее количество студентов"
    FROM STUDENTS;

-- Сколько преподавателей работает в институте?
SELECT COUNT(*) AS "Количество преподавателей"
    FROM TEACHERS;

-- Сколько всего групп?
SELECT COUNT(*) AS "Общее количество групп"
    FROM GROUPS;

-- Сколько групп на каждом курсе?
SELECT 
    C.CR_NO AS "Курс",
    COUNT(G.ID_NO) AS "Количество групп"
FROM COURSE C
LEFT JOIN GROUPS G ON C.ID_NO = G.ID_NO_CR
GROUP BY C.CR_NO
ORDER BY C.CR_NO;

-- Какие дисциплины ведёт каждый преподаватель?
SELECT 
    T.TE_NO AS "Код преподавателя",
    T.FULL_NAME AS "Преподаватель",
    STRING_AGG(S.SU_NO || ' - ' || S.SUBJECT, ', ' ORDER BY S.SU_NO) AS "Преподаваемые дисциплины (номер - название)"
FROM TEACHERS T
JOIN SUBJECTS S ON T.TE_NO = S.TE_NO
GROUP BY T.TE_NO, T.FULL_NAME
ORDER BY T.FULL_NAME;

-- Сколько студентов по каждой специальности?
SELECT 
    SP.SP_CODE AS "Код специальности",
    SP.SPECIALIZATION AS "Специальность",
    COUNT(ST.ST_NO) AS "Количество студентов"
FROM SPECIALIZATION SP
JOIN COURSE C ON SP.SP_CODE = C.SP_CODE
JOIN GROUPS G ON C.ID_NO = G.ID_NO_CR
JOIN STUDENTS ST ON G.ID_NO = ST.ID_NO_GR
GROUP BY SP.SP_CODE, SP.SPECIALIZATION
ORDER BY COUNT(ST.ST_NO) DESC;