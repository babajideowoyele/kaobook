#!/usr/bin/env python
"""Clean stopwords from topic_data.json"""

import json

# English stopwords (sklearn's default list plus common Twitter terms)
STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but',
    'by', 'can', 'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for',
    'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself',
    'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just',
    'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off', 'on', 'once',
    'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she',
    'should', 'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves',
    'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until',
    'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom',
    'why', 'will', 'with', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves',
    # Common Twitter terms
    'rt', 'via', 'amp', 'https', 'http', 'co',
}

def clean_keywords(keywords):
    """Remove stopwords from keywords list"""
    return [kw for kw in keywords if kw.lower() not in STOPWORDS]

def main():
    input_path = "ui/topic_data.json"
    output_path = "ui/topic_data.json"

    print(f"Loading {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Found {len(data['topics'])} topics")

    for topic in data['topics']:
        original = topic['keywords']
        # Use keybert keywords if available, otherwise clean the regular keywords
        if 'keybert' in topic and topic['keybert']:
            topic['keywords'] = topic['keybert']
        else:
            topic['keywords'] = clean_keywords(original)

        # Update topic name based on cleaned keywords
        topic['name'] = f"{topic['id']}_" + "_".join(topic['keywords'][:4])

        print(f"Topic {topic['id']}: {original[:5]} -> {topic['keywords'][:5]}")

    print(f"\nSaving to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print("Done!")

if __name__ == "__main__":
    main()
