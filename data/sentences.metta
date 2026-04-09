 {
    "sentences": [
      "Bob always played tennis."
    ],
    "statements": [
      "(: bob_name (Name bob_obj Bob) (STV 1.0 1.0))",
      "(: tennis (Name tennis_obj Tennis) (STV 1.0 1.0))",
      "(: bob_play_tennis (Play bob_obj tennis_obj) (STV 0.1 0.6))"
    ],
    "queries": [
      {
        "question": "What is the probability that Bob is playing tennis now?",
        "query": "(: $prf (And (Name $bob_obj Bob) (Name $tennis_obj Tennis) (Play $bob_obj $tennis_obj)) $tv)",
        "rules": [],
        "expected_answer": "The probablity should be around 5-20% with confidence that is not to high"
      }
    ]
  }

(sentences ("Bob always played tennis.")
 statments ((: bob_name (Name bob_obj Bob) (STV 1.0 1.0))
            (: tennis (Name tennis_obj Tennis) (STV 1.0 1.0))
            (: bob_play_tennis (Play bob_obj tennis_obj) (STV 0.1 0.6)))
 queries   ((question "What is the probability that Bob is playing tennis now?"
             query (: $prf (And (Name $bob_obj Bob) (Name $tennis_obj Tennis) (Play $bob_obj $tennis_obj)) $tv)
             rules ()
             expected_answer "The probablity should be around 5-20% with confidence that is not to high")))


(: every_sec_of_fight_i_hate (Implication (And (Time $t) (Second $t) (Fight $f) (Involved i $f) (During $t $f))
                                          (And (Hate $h) (Experiencer $h i) (Theme $h $f))) (STV 0.9 0.9))

(: every_sec_implies_alot (Implication (And (Time $t) (Second $t) ($activity $a) (During $t $a)
                                            ($emotion $e) (Experiencer $e $i) (Theme $e $a))
                                       (ALot $e))) (STV 0.8 0.8))
