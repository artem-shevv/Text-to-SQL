-- Какие оценки я получил на экзаменах за всё время обучения? 
SELECT
    unrolled.su_no,
    s.subject,
    unrolled.mark_st
FROM (
    SELECT
        E.id_no,
        E.st_no,
        su.su_no,
        m.mark_st
    FROM EXAMINATION E,
        UNNEST(E.su_no) WITH ORDINALITY AS su(su_no, idx),
        UNNEST(E.mark) WITH ORDINALITY AS m(mark_st, idx)
    WHERE E.st_no = '54868-4585' AND su.idx = m.idx
) AS unrolled
JOIN subjects s ON s.su_no = unrolled.su_no;

-- Какие оценки я получил на зачётах за всё время обучения? 
SELECT
    unrolled.su_no,
    s.subject,
    unrolled.check_status
FROM (
    SELECT
        A.id_no,
        A.st_no,
        su.su_no,
        cs.check_status
    FROM attestation A,
        UNNEST(A.su_no) WITH ORDINALITY AS su(su_no, idx),
        UNNEST(A.check_st) WITH ORDINALITY AS cs(check_status, idx)
    WHERE A.st_no = '54868-4585' AND su.idx = cs.idx
) AS unrolled
JOIN subjects s ON s.su_no = unrolled.su_no;

-- Кто мой куратор?
SELECT T.FULL_NAME 
    FROM STUDENTS S
    JOIN GROUPS G ON S.ID_NO_GR = G.ID_NO
    JOIN TEACHERS T ON G.CURATOR_NO = T.TE_NO
    WHERE S.ST_NO = '54868-4585';

-- Кто староста моей группы? 
SELECT S2.SURNAME, S2.NAME
    FROM STUDENTS S
    JOIN GROUPS G ON S.ID_NO_GR = G.ID_NO
    JOIN STUDENTS S2 ON G.HEAD_NO = S2.ST_NO
    WHERE S.ST_NO = '54868-4585';

-- Какой номер зачётки у меня по счёту в таблице?
WITH student_positions AS (
    SELECT 
        ST_NO,
        ROW_NUMBER() OVER () AS natural_order_position 
    FROM STUDENTS
)
SELECT 
    ST_NO AS student_id,
    natural_order_position
FROM student_positions
WHERE ST_NO = '54868-4585';

-- Какие у меня предметы на этом курсе?
-- Что за предметы я сейчас изучаю?
SELECT 
    S.SU_NO, 
    S.SUBJECT
    FROM STUDENTS ST
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
    JOIN UNNEST(C.LIST_SU_NO) AS course_subject_id ON TRUE  
    JOIN SUBJECTS S ON S.SU_NO = course_subject_id
    WHERE ST.ST_NO = '54868-4585';

-- Какие преподаватели ведут мои предметы на этом курсе?
-- Кто сейчас преподаёт мне? 
SELECT DISTINCT T.FULL_NAME, S.SUBJECT
    FROM STUDENTS ST
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
    JOIN UNNEST(C.LIST_SU_NO) AS subject_id ON TRUE
    JOIN SUBJECTS S ON S.SU_NO = subject_id
    JOIN TEACHERS T ON T.TE_NO = S.TE_NO
    WHERE ST.ST_NO = '54868-4585';

-- Какие номера телефонов у преподавателей моих текущих предметов?
-- Номера телефонов моих преподавателей
SELECT DISTINCT PL.PHONE_NUMBER
    FROM STUDENTS ST
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
    JOIN UNNEST(C.LIST_SU_NO) AS subject_id ON TRUE
    JOIN SUBJECTS S ON S.SU_NO = subject_id
    JOIN PHONE_LIST PL ON PL.TE_NO = S.TE_NO
    WHERE ST.ST_NO = '54868-4585';

-- Кто преподавал мне "Машинное обучение"?
SELECT T.FULL_NAME
    FROM SUBJECTS S
    JOIN TEACHERS T ON S.TE_NO = T.TE_NO
    WHERE S.SUBJECT = 'Машинное обучение';   

-- Где я проживаю согласно данным в системе?
-- Где я живу?
SELECT ADDRESS FROM STUDENTS_INFO WHERE ST_NO = '54868-4585';

-- Когда у меня день рождения?
SELECT BIRTHDAY FROM STUDENTS_INFO WHERE ST_NO = '54868-4585';

-- В какой я группе и на каком курсе?
SELECT GR_NO, CR_NO FROM STUDENTS_INFO WHERE ST_NO = '0268-0955';

-- Какие у меня есть телефоны, занесённые в базу?
-- Какой у меня номер телефона?
SELECT PHONE_NUMBER FROM PHONE_LIST WHERE ST_NO = '54868-4585';

-- Какие предметы мне предстоит сдавать на следующем курсе? 
-- Что я буду изучать на следующем курсе?
SELECT S.SU_NO, S.SUBJECT
    FROM STUDENTS ST
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
    JOIN COURSE NEXT_C ON NEXT_C.CR_NO = C.CR_NO + 1 AND NEXT_C.SP_CODE = C.SP_CODE
    JOIN UNNEST(NEXT_C.LIST_SU_NO) AS next_subject_id ON TRUE
    JOIN SUBJECTS S ON S.SU_NO = next_subject_id
    WHERE ST.ST_NO = '54868-4585';

-- Какие предметы я сдавал на прошлом курсе? 
-- Что я изучал на прошлом курсе?
SELECT S.SU_NO, S.SUBJECT
    FROM STUDENTS ST
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
    JOIN COURSE NEXT_C ON NEXT_C.CR_NO = C.CR_NO - 1 AND NEXT_C.SP_CODE = C.SP_CODE
    JOIN UNNEST(NEXT_C.LIST_SU_NO) AS next_subject_id ON TRUE
    JOIN SUBJECTS S ON S.SU_NO = next_subject_id
    WHERE ST.ST_NO = '54868-4585';


-- Сколько студентов в моей группе?
SELECT array_length(G.LIST_ST_NO, 1) AS count_students
    FROM STUDENTS ST
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    WHERE ST.ST_NO = '54868-4585';


-- Какие оценки я получил на прошлом курсе?
-- Мои оценки за прошлый курс?
WITH exam_subjects AS (
    -- Разбираем массив предметов-экзаменов с их порядковыми номерами
    SELECT 
        unnest(E.SU_NO) AS su_no,
        unnest(E.MARK)::TEXT AS grade,
        'Exam' AS type,
        row_number() OVER () AS exam_order
    FROM EXAMINATION E
    WHERE E.ST_NO = '55154-0904'
),

attestation_subjects AS (
    -- Разбираем массив предметов-зачётов с их порядковыми номерами
    SELECT 
        unnest(A.SU_NO) AS su_no,
        unnest(A.CHECK_ST) AS grade,
        'Attestation' AS type,
        row_number() OVER () AS attest_order
    FROM ATTESTATION A
    WHERE A.ST_NO = '55154-0904'
),

previous_course_subjects AS (
    -- Получаем список предметов прошлого курса
    SELECT 
        s.su_no,
        s.ord
    FROM STUDENTS ST
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
    JOIN COURSE PREV_C ON PREV_C.CR_NO = C.CR_NO - 1 AND PREV_C.SP_CODE = C.SP_CODE
    JOIN LATERAL UNNEST(PREV_C.LIST_SU_NO) WITH ORDINALITY AS s(su_no, ord) ON TRUE
    WHERE ST.ST_NO = '55154-0904'
),

combined_results AS (
    -- Соединяем предметы прошлого курса с оценками
    SELECT 
        pc.su_no,
        S.SUBJECT,
        CASE 
            WHEN es.su_no IS NOT NULL THEN 'Exam'
            ELSE 'Attestation'
        END AS type,
        COALESCE(es.grade, asub.grade) AS grade
    FROM previous_course_subjects pc
    LEFT JOIN exam_subjects es ON pc.su_no = es.su_no
    LEFT JOIN attestation_subjects asub ON pc.su_no = asub.su_no
    JOIN SUBJECTS S ON S.SU_NO = pc.su_no
)

SELECT * FROM combined_results
ORDER BY su_no;




-- Дай мне список всех моих оценок за все курсы
-- Мои оценки за всё время обучения
-- Выведи весь список моих оценок
WITH student_courses AS (
    -- Получаем все курсы, которые изучал студент
    SELECT 
        C.ID_NO,
        C.CR_NO,
        C.SP_CODE
    FROM STUDENTS ST
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
    WHERE ST.ST_NO = '61957-2022'
),

all_exam_grades AS (
    -- Все оценки за экзамены
    SELECT 
        unnest(E.SU_NO) AS su_no,
        unnest(E.MARK)::TEXT AS grade,
        'Exam' AS type,
        sc.CR_NO AS course_number
    FROM EXAMINATION E
    JOIN student_courses sc ON E.ST_NO = '61957-2022'
),

all_attestation_grades AS (
    -- Все оценки за зачёты
    SELECT 
        unnest(A.SU_NO) AS su_no,
        unnest(A.CHECK_ST) AS grade,
        'Attestation' AS type,
        sc.CR_NO AS course_number
    FROM ATTESTATION A
    JOIN student_courses sc ON A.ST_NO = '61957-2022'
),

combined_grades AS (
    -- Объединяем все оценки
    SELECT 
        g.su_no,
        S.SUBJECT,
        g.type,
        g.grade,
        g.course_number,
        SP.SPECIALIZATION
    FROM (
        SELECT * FROM all_exam_grades
        UNION ALL
        SELECT * FROM all_attestation_grades
    ) g
    JOIN SUBJECTS S ON S.SU_NO = g.su_no
    JOIN SPECIALIZATION SP ON SP.SP_CODE = (
        SELECT SP_CODE FROM COURSE WHERE CR_NO = g.course_number LIMIT 1
    )
)

SELECT 
    su_no AS "Код предмета",
    SUBJECT AS "Предмет",
    type AS "Тип",
    grade AS "Оценка"
FROM combined_grades
ORDER BY course_number, type, su_no;


-- Кто был руководителем моего предыдущего курса?
SELECT C.DIR_NO, T.FULL_NAME
    FROM STUDENTS ST
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    JOIN COURSE CURRENT_C ON G.ID_NO_CR = CURRENT_C.ID_NO
    JOIN COURSE C ON C.CR_NO = CURRENT_C.CR_NO - 1 AND C.SP_CODE = CURRENT_C.SP_CODE
    JOIN TEACHERS T ON C.DIR_NO = T.TE_NO
    WHERE ST.ST_NO = '52584-207';



-- Какие предметы у меня будут за всё время обучения на этом направлении подготовки?
-- Что я изучу за время обучения на своём направлении?
-- Кто будет вести каждую дисциплину на каждом курсе моего обучения?
WITH student_info AS (
    -- Получаем информацию о студенте и его направлении подготовки
    SELECT 
        ST.ST_NO,
        G.ID_NO AS group_id,  
        C.SP_CODE
    FROM STUDENTS ST
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
    WHERE ST.ST_NO = '55154-0904'  
)

SELECT 
    S.SU_NO AS "Код предмета",
    S.SUBJECT AS "Название предмета",
    C.CR_NO AS "Курс",
    CASE 
        WHEN (ord % 2) = 1 THEN 'Exam'
        ELSE 'Attestation'
    END AS "Тип предмета",
    T.FULL_NAME AS "Преподаватель"
FROM student_info si
JOIN COURSE C ON C.SP_CODE = si.SP_CODE
JOIN LATERAL UNNEST(C.LIST_SU_NO) WITH ORDINALITY AS subjects(su_no, ord) ON TRUE
JOIN SUBJECTS S ON S.SU_NO = subjects.su_no
LEFT JOIN TEACHERS T ON S.TE_NO = T.TE_NO
ORDER BY C.CR_NO, subjects.ord;

---------------------------------------------------------------------------------------------------------------------------------------------------------