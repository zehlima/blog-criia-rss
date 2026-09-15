from dashboard.full_export import normalize_ranks,public,body

def test_normalization_preserves_all_evidence_not_only_first_five():
    rows={'Globo':{'publications':20,'ranking':[{'label':'A','evidence':[{'id':i} for i in range(20)]}], 'subject_ranking':[]}}
    result=normalize_ranks(rows)
    assert result['Globo']['ranking'][0]['article_ids']==list(range(20))
    assert result['Globo']['publications']==20

def test_export_never_contains_private_object_keys():
    assert public({'content_key':'private','nested':[{'report_key':'private','id':1}]})=={'nested':[{'id':1}]}

def test_unavailable_body_preserves_summary_and_does_not_claim_full_text():
    value=body(None,{'id':1,'summary':'RSS summary'})
    assert value['text'] is None
    assert value['summary']=='RSS summary'
    assert value['text_basis']=='title_summary'
