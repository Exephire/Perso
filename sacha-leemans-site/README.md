# Sacha Leemans Créations — maquette du site

Maquette fonctionnelle et responsive d'un site vitrine + e-commerce pour [@sachaleemanscreations](https://www.instagram.com/sachaleemanscreations/).
Un seul fichier, sans dépendance : ouvrir `index.html` dans un navigateur.

## Pages et fonctions
- **Accueil** : hero, réassurance, collections, nouveautés, savoir-faire, appel au sur-mesure, avis, grille Instagram, newsletter (code `BIENVENUE10`).
- **Boutique** : filtres par catégorie, recherche (sans accents), tri, filtre « en stock ».
- **Fiche produit** : galerie, options (finition, taille, coloris, avec variation de prix), gravure d'initiales (+5 €), quantité limitée au stock, alerte de retour en stock, produits associés.
- **Panier** (tiroir) : quantités, code promo, barre « livraison offerte dès 60 € ».
- **Commande en 3 étapes** : coordonnées → livraison (domicile / point relais / retrait atelier, emballage cadeau) → paiement (redirection prestataire simulée) → confirmation.
- **Sur-mesure** (formulaire de demande de devis avec images), **L'atelier**, **Contact + FAQ**, **Favoris**.
- Pages légales (modèles à compléter), bannière cookies, panier et favoris gardés sur l'appareil, mode sombre automatique.

## À remplacer avant mise en ligne
- Catalogue : tableau `P` (produits) et `CATS` (catégories) dans le script.
- Visuels : les illustrations générées (`art()`) tiennent la place des vraies photos produit.
- Textes de l'atelier, avis clientes, e-mail de contact, mentions légales et CGV.

## Passage en production conseillé
- **Shopify** (le plus simple pour un site clé en main) : reprendre cette maquette en thème, paiements Shopify Payments / Bancontact / PayPal.
- Alternative : **WooCommerce** ou un front statique + **Stripe Checkout** / **Mollie**.
