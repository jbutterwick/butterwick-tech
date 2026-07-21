+++
title = "frishy.net"
date = 2026-02-03

[taxonomies]
categories = ["software"]

[extra]
living = true
+++
# frishy.net

frishy.net is a fish data logger for anglers with community features.
<!-- more -->
One of my 2026 resolutions was to get out fishing more often. I hadn't been fishing in a while, and since the last time 
I've been, I've developed a healthy appreciation for nature. One of the things about nature that interests me the most
is the absolute importance of a healthy food chain. The sun is always shining down on us, but there needs to be a healthy
population of plants to turn that sunlight into stored energy in order to build a base in the food chain. Without 
photosynthesizers, the environment has no way of transferring energy into the higher trophic levels. So, measuring the 
populations of the different levels of the food chain has become something I'm deeply interested in doing.

I use [iNaturalist](https://www.inaturalist.org/people/jbutterwick) when I'm out and about to mark down my observations of 
nature. It's fun sharing them with the world and I like to think I'm contributing to a higher cause when I use it.

I had an urge while out fishing to log my fish, as well as data like length and weight and what tackle I was using. 
iNaturalist isn't really built for this kind of logging, although you could probably just add those details as notes
on your observations, and you wouldn't be any worse off. But that's not a solution for people who don't use iNaturalist, 
and I wanted to come up with something that my friends or grandparents would like to use. Thus, frishy.net was born.

## here frishy frishy

In [frishy.net](https://frishy.net/) you can:
- log a catch, including:
  - location
  - time of day
  - species
  - a photo gallery
  - length
  - weight
  - what tackle or bait you used
- message and follow other anglers
- search for fish, tackle, or anglers
- see a map of catches
- lookup species data like:
  - species
  - range maps
  - description
  - taxonomy
  - photos
  - all catches in frishy, in list or map form
  - what time of day a species is most often caught at
  - what tackle is used to catch this species

frishy uses an Express.js backend and a vanilla JS SPA frontend. It uses SQLite 3 to store data, and the VPS' filesystem
for images. It runs in a Linode right now, but I'm planning on migrating it to my home lab soon. Its repository is 
currently private, and is likely to remain so. That may change in the future, however.

This project has been such a thrill to me. It came together very quickly, and it was a joy to flex some product muscle 
that I've been holding back for a long time now.
