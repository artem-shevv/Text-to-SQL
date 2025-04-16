--Сколько студентов я обучаю?
SELECT SUM(array_length(G.LIST_ST_NO, 1)) AS total_students
    FROM SUBJECTS S
    JOIN TEACHERS T ON S.TE_NO = T.TE_NO
    JOIN COURSE C ON S.SU_NO = ANY(C.LIST_SU_NO)
    JOIN GROUPS G ON C.ID_NO = G.ID_NO_CR
    WHERE T.TE_NO = '80-014-3241';




--Кто из студентов изучает мой предмет "Нейронные сети"?
SELECT ST.ST_NO, ST.SURNAME, ST.NAME
    FROM STUDENTS ST
    JOIN STUDENTS_INFO SI ON ST.ST_NO = SI.ST_NO
    JOIN GROUPS G ON ST.ID_NO_GR = G.ID_NO
    JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
    JOIN UNNEST(C.LIST_SU_NO) AS subject_id ON TRUE
    JOIN SUBJECTS S ON S.SU_NO = subject_id
    WHERE S.SUBJECT = 'Neural Networks';




-- Какие у меня есть телефоны, занесённые в базу?
-- Какой у меня номер телефона?
SELECT PHONE_NUMBER FROM PHONE_LIST WHERE TE_NO = '08-731-2673';


--На каком направлении подготовки я преподаю?
SELECT DISTINCT C.SP_CODE
    FROM SUBJECTS S
    JOIN TEACHERS T ON S.TE_NO = T.TE_NO
    JOIN COURSE C ON S.SU_NO = ANY(C.LIST_SU_NO)
    WHERE T.TE_NO = '08-731-2673';






--Какие предметы я веду?
SELECT S.SU_NO, S.SUBJECT
    FROM SUBJECTS S
    JOIN TEACHERS T ON S.TE_NO = T.TE_NO
    WHERE T.TE_NO = '08-731-2673';





--Какие курсы содержат мои предметы?
SELECT DISTINCT C.ID_NO,C.CR_NO, C.SP_CODE
    FROM SUBJECTS S
    JOIN COURSE C ON S.SU_NO = ANY(C.LIST_SU_NO)
    JOIN TEACHERS T ON S.TE_NO = T.TE_NO
    WHERE T.TE_NO = '62-180-5657'
    ORDER BY C.ID_NO,C.CR_NO;



--я преподаватель 62-180-5657, общая информация
SELECT 
    T.TE_NO,
    T.FULL_NAME,
    COALESCE((SELECT string_agg(P.PHONE_NUMBER, ', ') 
               FROM PHONE_LIST P 
               WHERE P.TE_NO = T.TE_NO), 'Не указан') AS phone_numbers,
    COUNT(DISTINCT ST.ST_NO) AS total_students
FROM 
    TEACHERS T
LEFT JOIN 
    SUBJECTS S ON T.TE_NO = S.TE_NO
LEFT JOIN 
    COURSE C ON S.SU_NO = ANY(C.LIST_SU_NO)
LEFT JOIN 
    GROUPS G ON C.ID_NO = G.ID_NO_CR
LEFT JOIN 
    UNNEST(G.LIST_ST_NO) AS student_id ON TRUE
LEFT JOIN 
    STUDENTS ST ON student_id = ST.ST_NO
WHERE 
    T.TE_NO = '62-180-5657'
GROUP BY 
    T.TE_NO, T.FULL_NAME;







--В каких группах я являюсь куратором?
SELECT
    G.ID_NO,
    G.GR_NO,
    G.LIST_ST_NO,
    G.HEAD_NO
FROM 
    GROUPS G
WHERE 
    G.CURATOR_NO = '18-890-4144';





--Кто является старостой группы, где я куратор?
SELECT S.ST_NO,S.SURNAME, S.NAME
    FROM GROUPS G
    JOIN STUDENTS S ON G.HEAD_NO = S.ST_NO
    WHERE G.CURATOR_NO = '18-890-4144';





--Кто является куратором группы id=5?
SELECT T.FULL_NAME, G.CURATOR_NO 
    FROM GROUPS G 
    JOIN TEACHERS T ON G.CURATOR_NO = T.TE_NO
    WHERE G.ID_NO = 5;





--Куратором каких групп является абанин александр васильевич? 
SELECT G.ID_NO, G.GR_NO, G.LIST_ST_NO, G.HEAD_NO
    FROM GROUPS G
    JOIN TEACHERS T ON G.CURATOR_NO = T.TE_NO
    WHERE T.FULL_NAME = 'Abanin Alexander Vasilyevich';






--какие предметы ведёт мелихов сергей николаевич?
SELECT S.SUBJECT
    FROM SUBJECTS S
    JOIN TEACHERS T ON S.TE_NO = T.TE_NO
    WHERE T.FULL_NAME = 'Melikhov Sergey Nikolaevich';







--В каких группах учатся студенты, которым я читаю предметы?
SELECT G.ID_NO as id_no_gr, G.GR_NO, C.CR_NO, array_length(G.LIST_ST_NO, 1) AS total_students
    FROM GROUPS G
    JOIN COURSE C ON G.ID_NO_CR = C.ID_NO
    JOIN SUBJECTS S ON S.SU_NO = ANY(C.LIST_SU_NO)
    WHERE S.TE_NO = '18-890-4144'
    GROUP BY G.ID_NO, G.GR_NO, C.CR_NO;






---------------------------------------------------------------------------------------------------------------------------------------------------------



--Какие оценки получили студенты по моему предмету/предметам?
WITH 
-- Получаем все предметы преподавателя
teacher_subjects AS (
    SELECT 
        SU_NO::bigint AS SU_NO,  -- Явное приведение к bigint
        SUBJECT
    FROM 
        SUBJECTS
    WHERE 
        TE_NO = '62-180-5657'
),

-- Разворачиваем экзаменационные оценки
exploded_exams AS (
    SELECT
        e.ST_NO,
        unnest(e.SU_NO)::bigint AS SU_NO,  -- Явное приведение к bigint
        unnest(e.MARK)::text AS grade
    FROM
        EXAMINATION e
    JOIN
        teacher_subjects ts ON ts.SU_NO = ANY(e.SU_NO)
),

-- Разворачиваем зачетные оценки
exploded_attestations AS (
    SELECT
        a.ST_NO,
        unnest(a.SU_NO)::bigint AS SU_NO,  -- Явное приведение к bigint
        unnest(a.CHECK_ST) AS grade
    FROM
        ATTESTATION a
    JOIN
        teacher_subjects ts ON ts.SU_NO = ANY(a.SU_NO)
),

-- Группируем экзаменационные оценки
grouped_exams AS (
    SELECT
        ST_NO,
        SU_NO,
        string_agg(grade, ', ') AS grades
    FROM
        exploded_exams
    GROUP BY
        ST_NO, SU_NO
),

-- Группируем зачетные оценки
grouped_attestations AS (
    SELECT
        ST_NO,
        SU_NO,
        string_agg(grade, ', ') AS grades
    FROM
        exploded_attestations
    GROUP BY
        ST_NO, SU_NO
)

-- Финальный запрос с явными приведениями типов
SELECT
    ts.SUBJECT,
    s.ST_NO AS student_id,
    s.SURNAME || ' ' || s.NAME AS student_name,
    COALESCE(ge.grades, '') || 
    CASE WHEN ge.grades IS NOT NULL AND ga.grades IS NOT NULL THEN ', ' ELSE '' END || 
    COALESCE(ga.grades, '') AS all_grades
FROM
    STUDENTS s
LEFT JOIN grouped_exams ge ON s.ST_NO = ge.ST_NO
LEFT JOIN grouped_attestations ga ON s.ST_NO = ga.ST_NO AND ge.SU_NO::bigint = ga.SU_NO::bigint
JOIN teacher_subjects ts ON ts.SU_NO = COALESCE(ge.SU_NO, ga.SU_NO)::bigint
ORDER BY
    ts.SUBJECT,
    student_name









--Сколько всего студентов за последние два года получили 5 за экзамен
WITH 
-- Получаем текущий курс каждого студента
current_courses AS (
    SELECT 
        ST_NO,
        CR_NO AS current_course
    FROM 
        STUDENTS_INFO
),

-- Получаем студентов с оценками 5 за последние 2 года (последние 4 оценки)
WITH 
-- Получаем текущий курс каждого студента
current_courses AS (
    SELECT 
        ST_NO,
        CR_NO AS current_course
    FROM 
        STUDENTS_INFO
),

-- Получаем студентов с оценками 5 за последние 2 года (последние 4 оценки)
students_with_fives AS (
    SELECT 
        e.ST_NO,
        s.SURNAME || ' ' || s.NAME AS student_name,
        si.CR_NO AS course,
        si.GR_NO AS group_number,
        -- Количество пятерок в последних 4 оценках
        (SELECT COUNT(*) 
         FROM unnest(e.MARK) WITH ORDINALITY AS m(grade, idx)
         WHERE m.grade = 5 AND m.idx > array_length(e.MARK, 1) - 4) AS five_count
    FROM 
        EXAMINATION e
    JOIN 
        STUDENTS s ON e.ST_NO = s.ST_NO
    JOIN 
        STUDENTS_INFO si ON e.ST_NO = si.ST_NO
    JOIN 
        current_courses cc ON e.ST_NO = cc.ST_NO
    WHERE 
        -- Только текущий и предыдущий курсы
        si.CR_NO BETWEEN cc.current_course - 1 AND cc.current_course
        -- Проверяем, есть ли хотя бы одна 5 в последних 4 оценках
        AND EXISTS (
            SELECT 1 
            FROM unnest(e.MARK) WITH ORDINALITY AS m(grade, idx)
            WHERE m.grade = 5 AND m.idx > array_length(e.MARK, 1) - 4
        )
)

-- Итоговый результат с информацией о группе и курсе
SELECT 
    ST_NO AS student_id,
    student_name,
    group_number,
    course
FROM 
    students_with_fives
WHERE 
    five_count > 0
GROUP BY 
    ST_NO, student_name, group_number, course
ORDER BY 
    group_number,
    course,
    student_name;








--Какие у меня есть контакты студентов-старост?
WITH 
teacher_id AS (
    SELECT '67-799-2605' AS te_no
),

-- 1. Где преподаватель - куратор группы (получаем старост этих групп)
group_curator_heads AS (
    SELECT 
        c.ID_NO AS course_id,
        c.CR_NO AS course_number,
        g.ID_NO AS group_id,
        g.GR_NO AS group_number,
        g.HEAD_NO AS head_id,
        s.SURNAME || ' ' || s.NAME AS head_name,
        'куратор группы' AS curator_role
    FROM 
        GROUPS g
    JOIN 
        COURSE c ON g.ID_NO_CR = c.ID_NO
    JOIN 
        STUDENTS s ON g.HEAD_NO = s.ST_NO
    CROSS JOIN 
        teacher_id t
    WHERE 
        g.CURATOR_NO = t.te_no
),

-- 2. Где преподаватель - куратор курса (получаем всех старост групп этого курса)
course_curator_heads AS (
    SELECT 
        c.ID_NO AS course_id,
        c.CR_NO AS course_number,
        g.ID_NO AS group_id,
        g.GR_NO AS group_number,
        g.HEAD_NO AS head_id,
        s.SURNAME || ' ' || s.NAME AS head_name,
        'куратор курса' AS curator_role
    FROM 
        COURSE c
    JOIN 
        GROUPS g ON g.ID_NO_CR = c.ID_NO
    JOIN 
        STUDENTS s ON g.HEAD_NO = s.ST_NO
    CROSS JOIN 
        teacher_id t
    WHERE 
        c.DIR_NO = t.te_no
),

-- Объединяем оба типа
all_heads AS (
    SELECT * FROM group_curator_heads
    UNION ALL
    SELECT * FROM course_curator_heads
),

-- Добавляем телефоны старост
heads_with_phones AS (
    SELECT 
        ah.*,
        (
            SELECT string_agg(pl.PHONE_NUMBER, ', ')
            FROM PHONE_LIST pl
            WHERE pl.ST_NO = ah.head_id
        ) AS head_phones
    FROM 
        all_heads ah
)

-- Итоговый результат
SELECT 
    course_id,
    course_number,
    group_id,
    group_number,
    head_id,
    head_name,
    head_phones,
    curator_role
FROM 
    heads_with_phones
ORDER BY
    curator_role DESC,  -- Сначала кураторы групп, затем курсов
    course_id,
    group_number;








--Кто из студентов не сдал мой предмет?(получил 2 в случае экзамена или "Не сдал" в случае зачёта)
WITH 
-- ID преподавателя (замените на нужный)
teacher_id AS (
    SELECT '62-180-5657' AS te_no
),

-- Предметы преподавателя
teacher_subjects AS (
    SELECT 
        s.SU_NO,
        s.SUBJECT
    FROM 
        SUBJECTS s
    CROSS JOIN 
        teacher_id t
    WHERE 
        s.TE_NO = t.te_no
),

-- Развернутые экзамены с сопоставлением предметов и оценок
expanded_exams AS (
    SELECT 
        e.ST_NO,
        e.SU_NO[subject_idx] AS subject_id,
        e.MARK[mark_idx] AS mark,
        subject_idx
    FROM 
        EXAMINATION e,
        generate_subscripts(e.SU_NO, 1) AS subject_idx,
        generate_subscripts(e.MARK, 1) AS mark_idx
    WHERE 
        subject_idx = mark_idx  -- Сопоставляем предметы и оценки по индексу
),

-- Несданные экзамены по предметам преподавателя
failed_exams AS (
    SELECT DISTINCT
        ee.ST_NO AS student_id,
        st.SURNAME || ' ' || st.NAME AS student_name,
        ts.SU_NO AS subject_id,
        ts.SUBJECT AS subject_name,
        si.CR_NO AS course_number,
        si.GR_NO AS group_number,
        '2 (экзамен)' AS result
    FROM 
        expanded_exams ee
    JOIN 
        teacher_subjects ts ON ee.subject_id = ts.SU_NO
    JOIN 
        STUDENTS st ON ee.ST_NO = st.ST_NO
    JOIN 
        STUDENTS_INFO si ON ee.ST_NO = si.ST_NO
    WHERE 
        ee.mark = 2
),

-- Развернутые зачеты с сопоставлением предметов и оценок
expanded_attestations AS (
    SELECT 
        a.ST_NO,
        a.SU_NO[subject_idx] AS subject_id,
        a.CHECK_ST[check_idx] AS check_result,
        subject_idx
    FROM 
        ATTESTATION a,
        generate_subscripts(a.SU_NO, 1) AS subject_idx,
        generate_subscripts(a.CHECK_ST, 1) AS check_idx
    WHERE 
        subject_idx = check_idx  -- Сопоставляем предметы и оценки по индексу
),

-- Несданные зачеты по предметам преподавателя
failed_attests AS (
    SELECT DISTINCT
        ea.ST_NO AS student_id,
        st.SURNAME || ' ' || st.NAME AS student_name,
        ts.SU_NO AS subject_id,
        ts.SUBJECT AS subject_name,
        si.CR_NO AS course_number,
        si.GR_NO AS group_number,
        'Не сдал (зачёт)' AS result
    FROM 
        expanded_attestations ea
    JOIN 
        teacher_subjects ts ON ea.subject_id = ts.SU_NO
    JOIN 
        STUDENTS st ON ea.ST_NO = st.ST_NO
    JOIN 
        STUDENTS_INFO si ON ea.ST_NO = si.ST_NO
    WHERE 
        (ea.check_result = 'Not passed')
)

-- Объединяем результаты
SELECT * FROM (
    SELECT * FROM failed_exams
    UNION ALL
    SELECT * FROM failed_attests
) combined_results
ORDER BY 
    subject_id,
    course_number,
    group_number,
    student_name,
    subject_name;








--Сколько студентов получили 5 по моему предмету?
WITH 
teacher_id AS (
    SELECT '62-180-5657'::text AS te_no
),

-- Предметы преподавателя
teacher_subjects AS (
    SELECT 
        s.SU_NO,
        s.SUBJECT
    FROM 
        SUBJECTS s
    CROSS JOIN 
        teacher_id t
    WHERE 
        s.TE_NO = t.te_no
),

-- Развернутые экзамены с точным сопоставлением предметов и оценок
expanded_exams AS (
    SELECT 
        e.ST_NO,
        e.SU_NO[subject_idx] AS subject_id,
        e.MARK[mark_idx] AS mark,
        subject_idx,
        mark_idx
    FROM 
        EXAMINATION e,
        generate_subscripts(e.SU_NO, 1) AS subject_idx,
        generate_subscripts(e.MARK, 1) AS mark_idx
    WHERE 
        subject_idx = mark_idx 
),

-- Добавляем информацию о курсе и группе
exams_with_info AS (
    SELECT 
        ee.*,
        si.CR_NO AS course_number,
        si.GR_NO AS group_number
    FROM 
        expanded_exams ee
    JOIN 
        STUDENTS_INFO si ON ee.ST_NO = si.ST_NO
),

-- Студенты с пятерками по предметам преподавателя
students_with_fives AS (
    SELECT 
        e.ST_NO AS student_id,
        s.SURNAME || ' ' || s.NAME AS student_name,
        ts.SUBJECT,
        e.course_number,
        e.group_number,
        COUNT(*) OVER (PARTITION BY ts.SUBJECT) AS subject_fives_count
    FROM 
        exams_with_info e
    JOIN 
        teacher_subjects ts ON e.subject_id = ts.SU_NO
    JOIN 
        STUDENTS s ON e.ST_NO = s.ST_NO
    WHERE 
        e.mark = 5
)

-- Итоговый результат
SELECT 
    student_id,
    student_name,
    SUBJECT,
    course_number,
    group_number,
    subject_fives_count AS total_fives_for_subject
FROM 
    students_with_fives
ORDER BY 
    SUBJECT,
    course_number,
    group_number,
    student_name;






--Кто из студентов сдавал мой предмет и на какую оценку?
WITH 
teacher_id AS (
    SELECT '62-180-5657' AS te_no
),

-- Предметы преподавателя
teacher_subjects AS (
    SELECT 
        s.SU_NO,
        s.SUBJECT
    FROM 
        SUBJECTS s
    CROSS JOIN 
        teacher_id t
    WHERE 
        s.TE_NO = t.te_no
),

-- Развернутые экзамены с точным сопоставлением предметов и оценок
expanded_exams AS (
    SELECT 
        e.ST_NO,
        e.SU_NO[subject_idx] AS subject_id,
        e.MARK[mark_idx] AS mark,
        subject_idx
    FROM 
        EXAMINATION e,
        generate_subscripts(e.SU_NO, 1) AS subject_idx,
        generate_subscripts(e.MARK, 1) AS mark_idx
    WHERE 
        subject_idx = mark_idx
),

-- Развернутые зачеты с точным сопоставлением
expanded_attestations AS (
    SELECT 
        a.ST_NO,
        a.SU_NO[subject_idx] AS subject_id,
        a.CHECK_ST[check_idx] AS result,
        subject_idx
    FROM 
        ATTESTATION a,
        generate_subscripts(a.SU_NO, 1) AS subject_idx,
        generate_subscripts(a.CHECK_ST, 1) AS check_idx
    WHERE 
        subject_idx = check_idx
),

-- Объединенные результаты с информацией о курсе
all_results AS (
    -- Экзаменационные оценки
    SELECT 
        ee.ST_NO,
        ts.SU_NO AS subject_no,  -- Добавлен номер предмета
        ts.SUBJECT,
        ee.mark::text AS grade,
        si.CR_NO AS course_number,
        'экзамен' AS exam_type
    FROM 
        expanded_exams ee
    JOIN 
        teacher_subjects ts ON ee.subject_id = ts.SU_NO
    JOIN 
        STUDENTS_INFO si ON ee.ST_NO = si.ST_NO
    
    UNION ALL
    
    -- Зачетные оценки
    SELECT 
        ea.ST_NO,
        ts.SU_NO AS subject_no,  -- Добавлен номер предмета
        ts.SUBJECT,
        ea.result AS grade,
        si.CR_NO AS course_number,
        'зачет' AS exam_type
    FROM 
        expanded_attestations ea
    JOIN 
        teacher_subjects ts ON ea.subject_id = ts.SU_NO
    JOIN 
        STUDENTS_INFO si ON ea.ST_NO = si.ST_NO
)

-- Итоговый результат с информацией о студентах
SELECT 
    s.ST_NO, 
    s.SURNAME || ' ' || s.NAME AS student_name,
    ar.subject_no,  
    ar.SUBJECT,     
    ar.course_number,
    si.GR_NO AS group_number,
    ar.grade,
    ar.exam_type
FROM 
    all_results ar
JOIN 
    STUDENTS s ON ar.ST_NO = s.ST_NO
JOIN 
    STUDENTS_INFO si ON ar.ST_NO = si.ST_NO
ORDER BY 
    ar.SUBJECT,
    ar.course_number,
    student_name;