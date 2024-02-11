def return_prompt(best_hit, query):

    if isinstance(best_hit, str):
        prompt = f"""
        Donot respond like 'by given context', 'in the text given' (or) 'based on the excerpt given'
        Excerpt from the article: 
        {best_hit}
        Question: {query}
        
        Extract the answer of the question from the text provided. 
        If the text doesn't contain the answer, 
        reply that the answer is not available."""

        return prompt
    elif isinstance(best_hit, list):
        prompts = []
        for num in range(len(best_hit)):
            prompt = f"""Excerpt from the article: 
            {best_hit[num]} 
            Question: {query[num]}
            Extract the answer of the question from the text provided. 
            If the text doesn't contain the answer, 
            reply that the answer is not available."""
            prompts.append(prompt)
        return prompts
