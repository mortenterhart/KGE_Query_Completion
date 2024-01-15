DROP TABLE csv_load_list;

CREATE TABLE csv_load_list (
    cl_file         VARCHAR, 
    cl_file_in_zip  VARCHAR,
    cl_state        INT DEFAULT 0, 
    cl_error        LONG VARCHAR, 
    cl_table        VARCHAR, 
    cl_options      ANY,
    cl_started      DATETIME, 
    cl_done         DATETIME,
    PRIMARY KEY (cl_file, cl_file_in_zip))
CREATE INDEX cl_state ON csv_load_list (cl_state)
;

CREATE PROCEDURE csv_cols_cb (
    INOUT  r    ANY, 
    IN     inx  INT, 
    INOUT  cbd  ANY)
{
  IF (cbd IS NULL)
    cbd := VECTOR ();
  cbd := vector_concat (cbd, VECTOR (r));   
}
;

CREATE PROCEDURE  csv_get_cols_array (
    INOUT  ss    ANY, 
    IN     hr    INT, 
    IN     offs  INT, 
    IN     opts  ANY)
{
  DECLARE h, res ANY;
  DECLARE inx, j, ncols, no_head INT;
  
  h := NULL;
  no_head := 0;
  IF (hr < 0)
    {
      no_head := 1;
      hr := 0;
    }
  IF (offs < 0)
    offs := 0;
  res := VECTOR ();
  csv_parse (ss, 'DB.DBA.csv_cols_cb', h, 0, offs + 10, opts);
  IF (h IS NOT NULL AND LENGTH (h) > offs)
    {
      DECLARE _row ANY;
      _row := h[hr];
      FOR (j := 0; j < LENGTH (_row); j := j + 1)           
        {
	  res := vector_concat (res, VECTOR (VECTOR (SYS_ALFANUM_NAME (CAST (_row[j] AS VARCHAR)), NULL)));
        }
      FOR (inx := offs; inx < LENGTH (h); inx := inx + 1)
       { 
	 _row := h[inx];
         FOR (j := 0; j < LENGTH (_row); j := j + 1)           
	   {
	     IF (res[j][1] IS NULL AND NOT (ISSTRING (_row[j]) AND _row[j] = '') AND _row[j] IS NOT NULL)
               res[j][1] := __tag (_row[j]);
             ELSE IF (__tag (_row[j]) <> res[j][1] AND 189 = res[j][1] AND (ISDOUBLE (_row[j]) OR isfloat (_row[j])))
	       res[j][1] := __tag (_row[j]);
             ELSE IF (__tag (_row[j]) <> res[j][1] AND ISINTEGER (_row[j]) AND (res[j][1] = 219 OR 190 = res[j][1]))
	       ;  
             ELSE IF (__tag (_row[j]) <> res[j][1])
               res[j][1] := -1;
	   }
       } 
    }
  FOR (inx := 0; inx < LENGTH (res); inx := inx + 1)
    { 
       IF (NOT ISSTRING (res[inx][0]) AND NOT ISNULL (res[inx][0]))
         no_head := 1;	
       ELSE IF (trim (res[inx][0]) = '' OR ISNULL (res[inx][0]))
         res[inx][0] := sprintf ('COL%d', inx);	 
    }  
  FOR (inx := 0; inx < LENGTH (res); inx := inx + 1)
    { 
       IF (res[inx][1] = -1 OR res[inx][1] IS NULL)
         res[inx][1] := 'VARCHAR';	 
       ELSE
         res[inx][1] := dv_type_title (res[inx][1]);	 
    }  
  IF (no_head)
    {
      FOR (inx := 0; inx < LENGTH (res); inx := inx + 1)
	{ 
	   res[inx][0] := sprintf ('COL%d', inx);
	}
    }
  RETURN res;
}
;

CREATE PROCEDURE csv_get_table_def (IN fn VARCHAR, IN f VARCHAR, IN opts ANY)
{
  DECLARE arr ANY;
  DECLARE s, r, ss ANY;
  DECLARE i, offs, st INT;

  IF (__tag (f) = 185)
    s := f;
  ELSE IF (f LIKE '%.gz')
    s := gz_file_open (f);
  ELSE
    s := file_open (f);
  st := 0; offs := 1; 
  IF (ISVECTOR (opts) AND MOD (LENGTH (opts), 2) = 0)
    {
      st := atoi (get_keyword ('header', opts, '0'));
      offs := atoi (get_keyword ('offset', opts, '1'));
    }  
  arr := csv_get_cols_array (s, st, offs, opts);   
  ss := string_output ();
  http (sprintf ('CREATE TABLE %s ( \n', fn), ss); 
  FOR (i := 0; i < LENGTH (arr); i := i + 1)
    {
       http (sprintf ('\t"%I" %s', arr[i][0], arr[i][1]), ss);
       IF (i < LENGTH (arr) - 1)
         http (', \n', ss);
    }
  http (')', ss);
  RETURN string_output_string (ss);  
}
;

CREATE PROCEDURE csv_register (IN path VARCHAR, IN mask VARCHAR)
{
  DECLARE ls ANY;
  DECLARE inx INT;
  ls := sys_dirlist (path, 1);
  FOR (inx := 0; inx < LENGTH (ls); inx := inx + 1)
    {
      IF (ls[inx] LIKE mask)
	{
	  IF (NOT (EXISTS (SELECT 1 FROM DB.DBA.CSV_LOAD_LIST WHERE CL_FILE = path || '/' || ls[inx] FOR UPDATE)))
	    {
	      DECLARE tbfile, ofile, tb, f, tbname VARCHAR;
	      DECLARE opts ANY;
	      tb := NULL; 
	      f := ls[inx];
	      tbfile := path || '/' || regexp_replace (f, '(\\.csv(\\.gz)?)|(\\.zip)', '') || '.tb';
	      ofile :=  path || '/' || regexp_replace (f, '(\\.csv(\\.gz)?)|(\\.zip)', '') || '.cfg';

	      opts := NULL;
	      IF (file_stat (ofile) <> 0)
		{
		  DECLARE delim, quot, header, offs, enc VARCHAR;
		  delim  := cfg_item_value (ofile, 'csv', 'csv-delimiter'); 
		  quot   := cfg_item_value (ofile, 'csv', 'csv-quote'); 
		  enc    := cfg_item_value (ofile, 'csv', 'encoding'); 
		  header := cfg_item_value (ofile, 'csv', 'header'); 
		  offs   := cfg_item_value (ofile, 'csv', 'offset'); 

		  IF (delim  IS NOT NULL) 
		    {
		      delim := REPLACE (delim, 'tab', '\t'); 
		      delim := REPLACE (delim, 'space', ' '); 
		      opts := vector_concat (opts, VECTOR ('csv-delimiter', delim));
		    }
		  IF (quot   IS NOT NULL) opts := vector_concat (opts, VECTOR ('csv-quote', quot));
		  IF (enc    IS NOT NULL) opts := vector_concat (opts, VECTOR ('encoding', enc));
		  IF (header IS NOT NULL) opts := vector_concat (opts, VECTOR ('header', header));
		  IF (offs   IS NOT NULL) opts := vector_concat (opts, VECTOR ('offset', offs));
		}

	      IF (file_stat (tbfile) <> 0)
		tbname := TRIM (file_to_string (tbfile), ' \r\n');
	      ELSE
		tbname := complete_table_name ('CSV.DBA.'||SYS_ALFANUM_NAME (f), 1);

              IF (EXISTS (SELECT 1 FROM SYS_KEYS WHERE KEY_TABLE = tbname))
		{
		  tb := tbname;
		}
	      ELSE
		{
		  IF (f LIKE '%.csv' OR f LIKE '%.csv.gz')
		    {
		      DECLARE stat, msg ANY;
		      stat := '00000';
		      DECLARE CONTINUE HANDLER FOR SQLSTATE '*' {
	                log_message (sprintf ('Cannot guess table name FOR file %s', f)); 		
		      };
		      {
		        EXEC (csv_get_table_def (tbname, path||'/'||f, opts), stat, msg);
			IF (stat = '00000')
		          tb := tbname;
			ELSE
		          log_message (sprintf ('Cannot guess table name FOR file %s', f));
	              } 		
		    }
		  ELSE IF (f LIKE '%.zip')
		    {
		      DECLARE ff, ss ANY;
		      ff := unzip_list (path || '/' || f);
		      FOREACH (ANY zf IN ff) DO
			{
			  IF (zf[1] > 0 AND zf[0] LIKE '%.csv')
			    {
			      ss := unzip_file (path || '/' || f, zf[0]);
			      tbname := complete_table_name ('CSV.DBA.'||SYS_ALFANUM_NAME (zf[0]), 1);
			      DECLARE stat, msg ANY;
			      tb := NULL;
			      stat := '00000';
			      DECLARE CONTINUE HANDLER FOR SQLSTATE '*' {
				log_message (sprintf ('Cannot guess table name FOR zipped file %s', zf[0])); 		
			      };
			      {
				EXEC (csv_get_table_def (tbname, ss, opts), stat, msg);
				IF (stat = '00000')
				  tb := tbname;
				ELSE
				  log_message (sprintf ('Cannot guess table name FOR zipped file %s', zf[0]));
				IF (tb IS NOT NULL)
				  INSERT INTO DB.DBA.CSV_LOAD_LIST (cl_file, cl_file_in_zip, cl_table, cl_options) 
				      VALUES (path || '/' || f, zf[0], tb, opts);
			      } 		
			    }
			}
		      tb := NULL;
		    }
		  ELSE   
		    log_message (sprintf ('Cannot guess table name FOR file %s', f));
		}
              IF (tb IS NOT NULL)
                {		
		  INSERT INTO DB.DBA.CSV_LOAD_LIST (cl_file, cl_file_in_zip, cl_table, cl_options) 
		      VALUES (path || '/' || f, '', tb, opts);
		}
	    }
	  COMMIT WORK;
	}
    }
}
;

CREATE PROCEDURE 
csv_register_all (IN path VARCHAR, IN mask VARCHAR)
{
  DECLARE ls ANY;
  DECLARE inx INT;
  ls := sys_dirlist (path, 0);
  csv_register (path, mask);
  FOR (inx := 0; inx < LENGTH (ls); inx := inx + 1)
    {
      IF (ls[inx] <> '.' AND ls[inx] <> '..')
	{
	  csv_register_all (path||'/'||ls[inx], mask);
	}
    }
}
;

CREATE PROCEDURE
csv_ld_file (IN f VARCHAR, IN zf VARCHAR, IN tb VARCHAR, IN ld_mode INT, IN opts ANY)
{
  DECLARE ss ANY;
  DECLARE offs, st INT;
  st := 0; offs := 1; 
  DECLARE EXIT HANDLER FOR SQLSTATE '*' {
    ROLLBACK WORK;
    UPDATE DB.DBA.CSV_LOAD_LIST SET CL_STATE = 2, CL_DONE = NOW (), CL_ERROR = __sql_state || ' ' || __sql_message 
		WHERE CL_FILE = f AND CL_FILE_IN_ZIP = zf;
    COMMIT WORK;
    log_message (sprintf (' File %s error %s %s', f, __sql_state, __sql_message));
    RETURN;
  };
  IF (ISVECTOR (opts) AND MOD (LENGTH (opts), 2) = 0)
    {
      st := atoi (get_keyword ('header', opts, '0'));
      offs := atoi (get_keyword ('offset', opts, '1'));
    }  
  IF (f LIKE '%.zip' AND LENGTH (zf) = 0)
    {
      DECLARE ff ANY;
      ff := unzip_list (f);
      FOREACH (ANY zzf IN ff) DO
	{
	  IF (zzf[1] > 0 AND zzf[0] LIKE '%.csv')
	    {
	      ss := unzip_file (f, zzf[0]);
	      csv_load (ss, offs, NULL, tb, ld_mode, opts);
	    }
	}
    }
  ELSE IF (f LIKE '%.zip' AND LENGTH (zf) > 0)
    {
      ss := unzip_file (f, zf);
      csv_load (ss, offs, NULL, tb, ld_mode, opts);
    }
  ELSE IF (f LIKE '%.gz')
    {
      ss := gz_file_open (f);
      csv_load (ss, offs, NULL, tb, ld_mode, opts);
    }
  ELSE
    csv_load_file (f, offs, NULL, tb, ld_mode, opts);
}
;

CREATE PROCEDURE csv_ld_array ()
{
  DECLARE first, last, zfirst, zlast, arr, len, local, opt, zf ANY;
  DECLARE cr CURSOR FOR
      SELECT TOP 100 CL_FILE, CL_TABLE, CL_OPTIONS, CL_FILE_IN_ZIP 
        FROM DB.DBA.CSV_LOAD_LIST TABLE OPTION (INDEX cl_state) 
        WHERE CL_STATE = 0
	FOR UPDATE;
  DECLARE fill INT;
  DECLARE f, g VARCHAR;
  DECLARE r ANY;
  WHENEVER NOT FOUND GOTO done;
  first := 0;
  last := 0;
  arr := make_array (100, 'any');
  fill := 0;
  OPEN cr;
  len := 0;
  FOR (;;)
    {
      FETCH cr INTO f, g, opt, zf;
      IF (0 = first) { first := f; zfirst := zf; }
      last := f; zlast := zf;
      arr[fill] := VECTOR (f, g, opt, zf);
      len := len + CAST (file_stat (f, 1) as INT);
      fill := fill + 1;
      IF (len > 2000000)
	GOTO done;
    }
 done:
  IF (0 = first)
    RETURN 0;
  UPDATE CSV_LOAD_LIST SET cl_state = 1, cl_started = NOW () 
    WHERE cl_file >= first 
      AND cl_file <= last 
      AND CL_FILE_IN_ZIP >= zfirst 
      AND CL_FILE_IN_ZIP <= zlast;
  RETURN arr;
}
;


CREATE PROCEDURE csv_loader_run (IN max_files integer := NULL, IN log_enable INT := 2)
{
  DECLARE sec_delay float;
  DECLARE _f, _graph VARCHAR;
  DECLARE arr ANY;
  DECLARE xx, inx, tx_mode, ld_mode INT;
  ld_mode := log_enable;
  WHILE (1)
    {
      SET ISOLATION = 'repeatable';
      DECLARE EXIT HANDLER FOR SQLSTATE '40001' {
	ROLLBACK WORK;
        sec_delay := RND(1000)*0.001;
	log_message(sprintf('deadlock in loader, waiting %d milliseconds', CAST (sec_delay * 1000 AS INTEGER)));
	DELAY(sec_delay);
	GOTO again;
      };

     again:;

      IF (EXISTS (SELECT 1 FROM DB.DBA.CSV_LOAD_LIST WHERE CL_FILE = '##stop'))
	{
	  log_message ('File load stopped by rdf_load_stop.');
	  RETURN;
	}

      log_enable (tx_mode, 1);

      IF (max_files IS NOT NULL AND max_files <= 0)
        {
	  COMMIT WORK;
	  log_message ('Max_files reached. Finishing.');
          RETURN;
	}

      WHENEVER NOT FOUND GOTO looks_empty;

      --      log_message ('Getting next file.');
      SET ISOLATION = 'serializable';
      arr := csv_ld_array ();
      COMMIT WORK;
      IF (0 = arr)
	GOTO looks_empty;
      log_enable (ld_mode, 1);

      FOR (inx := 0; inx < 100; inx := inx + 1)
	{
	  IF (0 = arr[inx])
	    GOTO arr_done;
	  csv_ld_file (arr[inx][0], arr[inx][3], arr[inx][1], ld_mode, arr[inx][2]);
	  UPDATE DB.DBA.CSV_LOAD_LIST 
	      SET CL_STATE = 2, CL_DONE = CURDATETIME () 
	    WHERE CL_FILE = arr[inx][0] 
	      AND CL_FILE_IN_ZIP = arr[inx][3];
	}
    arr_done:
      log_enable (tx_mode, 1);

      IF (max_files IS NOT NULL) max_files := max_files - 100;

      COMMIT WORK;
    }

 looks_empty:
  COMMIT WORK;
  log_message ('No more files to load. Loader has finished,');
  RETURN;
}
;
