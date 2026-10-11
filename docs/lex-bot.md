# Lex V2 bot specification

The bot is created in the console (or your own CloudFormation); `template.yaml` only provides the
fulfilment Lambda and the permission for Lex to call it.

## Setup

1. Lex V2 console, create bot `EcoGuardBot`, language English (AU) or English (US). Use
   `en_US` unless you change `LEX_LOCALE_ID`.
2. Add the slot type and intents below.
3. For each intent, enable **fulfilment: use a Lambda function** and choose the
   `LexFulfilmentFunction` from the stack outputs.
4. Build, then create an alias (for example `live`).
5. Note the bot ID and alias ID, then redeploy: `sam deploy` with `LexBotId` and `LexBotAliasId`.
6. In AWS Academy, Lex may require the `LabRole`; if bot creation is blocked, try a personal account.

## Slot type `SpeciesType` (restrict to slot values)

| Value | Synonyms |
|---|---|
| fox | foxes, red fox |
| feral pig | pig, pigs, feral pigs, boar |
| cane toad | toad, toads, cane toads |
| rabbit | rabbits, bunny |
| cat | cats, kitten, feral cat, stray cat |
| dog | dogs, puppy |

Values must match the tag names produced by the model config (`classes`) because the fulfilment
Lambda searches by the resolved value.

## Intent `FindSpecies`

Slots: `Species` (`SpeciesType`, required), `MinCount` (`AMAZON.Number`, optional, default 1),
`Date` (`AMAZON.Date`, optional).

Sample utterances:
- Show me all photos of {Species}
- Show me all photos of {Species} spotted {Date}
- Find at least {MinCount} {Species}
- Any {Species} sightings
- Where are the {Species}

## Intent `LostPet`

Slots: `Species` (`SpeciesType`, required), `Colour` (custom type or `AMAZON.Color`, optional),
`Breed` (`AMAZON.AlphaNumeric`, optional).

Sample utterances:
- Help me find a lost {Colour} {Species}
- I lost my {Species}
- My {Colour} {Species} is missing
- Find my {Breed} {Species}

Colour and breed are matched against tags that people add manually, so tell users to tag sightings
("ginger", "labrador") from the Tags tab.

## Fulfilment response

The Lambda returns one `PlainText` message listing up to five links. The frontend turns URLs in
messages into clickable links. Add an image response card later if there is time.

## Test phrases for the demo

- "Show me all photos of foxes spotted yesterday"
- "Find at least 2 feral pigs"
- "Help me find a lost ginger cat"
