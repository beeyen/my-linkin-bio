const recipeList = document.querySelector("#recipe-list");
const recipes = JSON.parse(recipeList.dataset.recipes);
const recipeLabels = JSON.parse(recipeList.dataset.recipeLabels);
const recipeSearch = document.querySelector(".recipe-search");
const recipeSearchInput = document.querySelector("#recipe-search-input");
const recipeCount = document.querySelector(".recipe-count");
const recipeResultsStatus = document.querySelector(".recipe-results-status");
const prepTimeFilter = document.querySelector("#prep-time-filter");
const proteinFilter = document.querySelector("#protein-filter");
const recipeCards = [...document.querySelectorAll(".recipe-card")];
const recipeAccordions = [...document.querySelectorAll(".recipe-accordion")];
const favoriteButtons = [...document.querySelectorAll(".favorite-button")];
const favoriteStorageKey = "my-linkin-bio-favorite-recipes";

const loadFavoriteRecipes = () => {
  try {
    return new Set(JSON.parse(localStorage.getItem(favoriteStorageKey) || "[]"));
  } catch (error) {
    return new Set();
  }
};

const saveFavoriteRecipes = (favoriteRecipes) => {
  localStorage.setItem(favoriteStorageKey, JSON.stringify([...favoriteRecipes]));
};

const favoriteRecipes = loadFavoriteRecipes();

const updateFavoriteButton = (button, isFavorite) => {
  button.textContent = isFavorite ? "❤️" : "🤍";
  button.setAttribute("aria-pressed", String(isFavorite));
  const label = isFavorite ? recipeLabels.remove_favorite : recipeLabels.favorite_recipe;
  button.setAttribute("aria-label", label);
  button.setAttribute("title", label);
  button.classList.toggle("favorite-button--active", isFavorite);
};

favoriteButtons.forEach((button) => {
  const recipeId = Number(button.dataset.recipeId);
  updateFavoriteButton(button, favoriteRecipes.has(recipeId));

  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (favoriteRecipes.has(recipeId)) {
      favoriteRecipes.delete(recipeId);
    } else {
      favoriteRecipes.add(recipeId);
    }
    saveFavoriteRecipes(favoriteRecipes);
    updateFavoriteButton(button, favoriteRecipes.has(recipeId));
  });
});

recipeAccordions.forEach((accordion) => {
  accordion.addEventListener("toggle", () => {
    if (!accordion.open) {
      accordion.dataset.searchExpanded = "false";
      return;
    }
    if (accordion.dataset.searchExpanded === "true") {
      return;
    }
    recipeAccordions.forEach((otherAccordion) => {
      if (otherAccordion !== accordion && otherAccordion.open) {
        otherAccordion.open = false;
      }
    });
  });
});

const matchesFilters = (recipe) => {
  const selectedTime = prepTimeFilter.selectedOptions[0];
  const minMinutes = selectedTime.dataset.minMinutes ? Number(selectedTime.dataset.minMinutes) : null;
  const maxMinutes = selectedTime.dataset.maxMinutes ? Number(selectedTime.dataset.maxMinutes) : null;
  const matchesTime = (minMinutes === null || recipe.prep_minutes >= minMinutes)
    && (maxMinutes === null || recipe.prep_minutes <= maxMinutes);
  const selectedProtein = proteinFilter.selectedOptions[0];
  const matchesProtein = selectedProtein === proteinFilter.options[0]
    || recipe.protein === selectedProtein.value;
  return matchesTime && matchesProtein;
};

const applyRecipeFilters = () => {
  let visibleRecipeCount = 0;
  recipeCards.forEach((card, index) => {
    const isVisible = matchesFilters(recipes[index]);
    card.hidden = !isVisible;
    card.classList.remove("recipe-card--highlighted");
    if (isVisible) {
      visibleRecipeCount += 1;
    }
  });
  const countLabel = visibleRecipeCount === 1
    ? recipeLabels.recipes_shown_singular
    : recipeLabels.recipes_shown_plural;
  recipeCount.textContent = `${visibleRecipeCount}${countLabel}`;
};

const clearRecipeSearch = () => {
  recipeSearchInput.value = "";
  recipeResultsStatus.textContent = "";
  recipeAccordions.forEach((accordion) => {
    accordion.dataset.searchExpanded = "false";
    accordion.open = false;
  });
  recipeCards.forEach((card) => {
    card.hidden = false;
    card.classList.remove("recipe-card--highlighted");
  });
  applyRecipeFilters();
};

prepTimeFilter.addEventListener("change", clearRecipeSearch);
proteinFilter.addEventListener("change", clearRecipeSearch);
applyRecipeFilters();

recipeSearch.addEventListener("submit", (event) => {
  event.preventDefault();
  recipeCards.forEach((card) => card.classList.remove("recipe-card--highlighted"));
  recipeResultsStatus.textContent = "";
  recipeAccordions.forEach((accordion) => {
    accordion.dataset.searchExpanded = "false";
    accordion.open = false;
  });
  const query = recipeSearchInput.value.trim().toLocaleLowerCase();

  if (!query) {
    applyRecipeFilters();
    return;
  }

  const matchingRecipeIndices = recipes.reduce((matches, recipe, index) => {
    const ingredientMatches = recipe.ingredients.some((ingredient) =>
      ingredient.toLocaleLowerCase().includes(query),
    );
    if (matchesFilters(recipe) && ingredientMatches) {
      matches.push(index);
    }
    return matches;
  }, []);

  if (matchingRecipeIndices.length === 0) {
    recipeCards.forEach((card) => {
      card.hidden = true;
    });
    recipeCount.textContent = `0${recipeLabels.recipes_shown_plural}`;
    recipeResultsStatus.textContent = recipeLabels.no_recipe_found.replace("{query}", recipeSearchInput.value.trim());
    return;
  }

  const matchingRecipeIndexSet = new Set(matchingRecipeIndices);
  recipeCards.forEach((card, index) => {
    card.hidden = !matchingRecipeIndexSet.has(index);
  });
  const countLabel = matchingRecipeIndices.length === 1
    ? recipeLabels.recipes_shown_singular
    : recipeLabels.recipes_shown_plural;
  recipeCount.textContent = `${matchingRecipeIndices.length}${countLabel}`;

  matchingRecipeIndices.forEach((recipeIndex) => {
    const matchingCard = document.querySelector(`[data-recipe-index="${recipeIndex}"]`);
    const matchingAccordion = matchingCard.querySelector(".recipe-accordion");
    matchingCard.classList.add("recipe-card--highlighted");
    matchingAccordion.dataset.searchExpanded = "true";
    matchingAccordion.open = true;
  });

  const firstMatchingCard = document.querySelector(`[data-recipe-index="${matchingRecipeIndices[0]}"]`);
  firstMatchingCard.scrollIntoView({ behavior: "smooth", block: "center" });
  firstMatchingCard.focus({ preventScroll: true });
});

document.querySelectorAll(".copy-recipe-button").forEach((button) => {
  button.addEventListener("click", async () => {
    const card = button.closest(".recipe-card");
    const ingredients = [...card.querySelectorAll(".ingredient-list li")]
      .map((ingredient) => `- ${ingredient.textContent.trim()}`)
      .join("\\n");
    const recipeText = [
      card.querySelector(".recipe-title").textContent.trim(),
      card.querySelector(".recipe-time").textContent.trim(),
      card.querySelector(".recipe-description").textContent.trim(),
      `${recipeLabels.ingredients_heading}:`,
      ingredients,
      card.querySelector(".recipe-instructions").textContent.trim(),
    ].join("\\n\\n");
    const status = card.querySelector(".copy-status");

    try {
      await navigator.clipboard.writeText(recipeText);
      status.textContent = recipeLabels.recipe_copied;
    } catch (error) {
      status.textContent = recipeLabels.copy_failed;
    }
  });
});
