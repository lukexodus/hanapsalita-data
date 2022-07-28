USE hanapsalita;
SELECT * FROM tagalog_words;
SELECT * FROM tagalog_start_strict;
SELECT * FROM tagalog_end_strict;
SELECT * FROM tagalog_contain_strict;
SELECT * FROM tagalog_start_not_strict;
SELECT * FROM tagalog_end_not_strict;
SELECT * FROM tagalog_contain_not_strict;
SELECT COUNT(*) FROM tagalog_start_not_strict;
SELECT COUNT(*) FROM tagalog_start_strict;

DESCRIBE tagalog_words;
DESCRIBE tagalog_start_strict;
DESCRIBE tagalog_end_strict;
DESCRIBE tagalog_contain_strict;
DESCRIBE tagalog_start_not_strict;
DESCRIBE tagalog_end_not_strict;
DESCRIBE tagalog_contain_not_strict;