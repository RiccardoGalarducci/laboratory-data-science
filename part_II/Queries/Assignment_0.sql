--- ASSIGNMENT 0
--- For every subject, the number of correct answers of male and female students

SELECT [subjectid], [gender], SUM([iscorrect]) AS correct_answers
FROM [Group_13].[Answers] a, [Group_13].[Users] u
WHERE a.userid = u.userid
GROUP BY [subjectid], [gender]
ORDER BY [subjectid],[gender], correct_answers