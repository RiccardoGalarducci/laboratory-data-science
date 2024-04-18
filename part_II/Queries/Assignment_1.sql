--- ASSIGNMENT 1
--- A subject is said to be easy if it has more than 90% correct answers, 
--- while it is said to be hard if it has less than 20% correct answers. 
--- List every easy and hard subject, considering only subjects with more than 10 total answers.


WITH temp AS(
SELECT [subjectid], SUM([iscorrect]) AS correct_answers, 
                    COUNT(answerid) AS total_answer, 
                    100*SUM([iscorrect])/COUNT(answerid) AS perc
FROM [Group_13].[Answers]
GROUP BY [subjectid]
HAVING COUNT(answerid) > 10
)
SELECT [subjectid], perc
FROM temp
WHERE perc >= 90 OR perc <= 20
ORDER BY perc DESC