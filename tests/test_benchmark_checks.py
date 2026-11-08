from run_benchmark import check_answer


def test_french_unavailable_information_is_an_abstention():
    answer = "Je ne trouve aucune information sur les conditions météorologiques dans les documents disponibles."
    assert check_answer({"expected_behavior": "abstain"}, answer, [])["abstention_correct"]


def test_invented_weather_is_not_an_abstention():
    assert not check_answer({"expected_behavior": "abstain"}, "Il faisait beau à Lyon.", [])["abstention_correct"]
