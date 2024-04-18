-- ASSIGNMENT 1
-- Show the student that made the most mistakes for each country.

WITH temp AS (
    SELECT a.userid, g.country_name, 
    CASE WHEN [iscorrect]=1 THEN 0 ELSE 1 END AS incorrect_answers
    FROM [Group_13].[Answers] a, [Group_13].[Users] u, [Group_13].[Geography] g
    WHERE a.userid = u.userid AND u.geoid = g.geoid
), temp_1 AS(
    SELECT userid, country_name, SUM(incorrect_answers) AS tot_incorrect_answers
    FROM temp 
    GROUP BY userid, country_name
)
SELECT userid, country_name, tot_incorrect_answers,
       DENSE_RANK() OVER(PARTITION BY country_name ORDER BY tot_incorrect_answers DESC) AS rank_by_country
FROM temp_1
ORDER BY country_name, rank_by_country;

-- ASSIGNMENT 2
-- For each subject, show the student with the highest total correct answers.
WITH temp AS(
    SELECT userid, subjectid, SUM(iscorrect) AS tot_correct_answers
    FROM [Group_13].[Answers]
    GROUP BY userid, subjectid
)
SELECT userid, subjectid, tot_correct_answers,
       DENSE_RANK() OVER(PARTITION BY subjectid ORDER BY tot_correct_answers DESC) AS rank_by_subjectid
FROM temp
ORDER BY subjectid, tot_correct_answers

-- ASSIGNMENT 3
-- For each continent, show the student with the highest ratio between his 
-- total correct answers and the average correct answers of that continent.

WITH temp AS (
    SELECT a.userid, g.continent, SUM([iscorrect]) AS tot_correct_answers
    FROM [Group_13].[Answers] a, [Group_13].[Users] u, [Group_13].[Geography] g
    WHERE a.userid = u.userid AND u.geoid = g.geoid
    GROUP BY a.userid, g.continent
), temp_2 AS(
    SELECT userid, continent, tot_correct_answers, 
       AVG(tot_correct_answers) OVER( PARTITION BY continent) AS avg_continent,
       tot_correct_answers/AVG(tot_correct_answers) OVER( PARTITION BY continent) AS ratio
    FROM temp)
SELECT userid, continent, tot_correct_answers, ratio, avg_continent,
       DENSE_RANK() OVER(PARTITION BY continent ORDER BY ratio DESC) AS rank_ratio
FROM temp_2;