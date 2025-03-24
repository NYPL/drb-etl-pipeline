// // Helper class to provide data to different citation formats
// export default class CitationFormatter {
//   /** Generate metadata object containing all data for a citation to an edition
//    * @param {object} work The overall work record to cite
//    * @param {object} edition The specific edition record to cite
//    *
//    * @returns {object} Metadata block that can be consumed by citation components
//    */
//   static getCitationData(work: any, edition: any) {
//     const contributorExclusions = [
//       "author",
//       "editor",
//       "translator",
//       "illustrator",
//       "publisher",
//     ];
//     const workAgents = work.agents || [];
//     const editionAgents = edition.agents || [];
//     return {
//       title: edition.title ? edition.title : work.title,
//       sub_title: edition.sub_title,
//       agents: {
//         authors: CitationFormatter.getAgentsOfType(workAgents, "author"),
//         editors: CitationFormatter.getAgentsOfType(workAgents, "editor", [
//           // @ts-expect-error ts-migrate(2322) FIXME: Type 'string' is not assignable to type 'never'.
//           "author",
//         ]),
//         illustrators: CitationFormatter.getAgentsOfType(
//           workAgents,
//           "illustrator",
//           // @ts-expect-error ts-migrate(2322) FIXME: Type 'string' is not assignable to type 'never'.
//           ["author"]
//         ),
//         translators: CitationFormatter.getAgentsOfType(
//           workAgents,
//           "translator",
//           // @ts-expect-error ts-migrate(2322) FIXME: Type 'string' is not assignable to type 'never'.
//           ["author"]
//         ),
//         publishers: CitationFormatter.getAgentsOfType(
//           editionAgents,
//           "publisher"
//         ),
//         contributors: CitationFormatter.getAgentsOfType(
//           [...workAgents, ...editionAgents],
//           false,
//           // @ts-expect-error ts-migrate(2345) FIXME: Argument of type 'string[]' is not assignable to p... Remove this comment to see the full error message
//           contributorExclusions
//         ),
//       },
//       publication_year: edition.publication_date,
//       publication_place: edition.publication_place,
//       edition: edition.edition_statement,
//       volume: edition.volume,
//       series: work.series,
//       sourceLink: CitationFormatter.setLinkFields(edition.items),
//       isGovernmentDoc: CitationFormatter.isGovernmentReport(work.measurements),
//     };
//   }

//   /** Extract Agents with a specific role
//    * @param {array} agents Agent objects that have the roles attribute to be filtered
//    * @param {string} includeType Specific role to return agents for (e.g. author)
//    * @param {array} excludeTypes  List of roles to exclude agents for
//    *
//    * @returns {array} List of agent names that had matching role but none of the excluded roles
//    */
//   static getAgentsOfType(agents: any, includeType: any, excludeTypes = []) {
//     if (!agents) {
//       return [];
//     }
//     const typeAgents = agents.filter(
//       (a: any) =>
//         (!includeType || a.roles.indexOf(includeType) > -1) &&
//         (excludeTypes.length === 0 ||
//           // @ts-expect-error ts-migrate(2345) FIXME: Argument of type 'any' is not assignable to parame... Remove this comment to see the full error message
//           a.roles.filter((r: any) => excludeTypes.includes(r)).length === 0)
//     );
//     return typeAgents.map((a: any) => a.name);
//   }

//   /** Extract first available link to a digitized resource
//    * @param {array} items Items attached to the edition being cited
//    *
//    * @returns {object} Contains URI to first digital resource and date it was last modified in SFR
//    */
//   static setLinkFields(items: any) {
//     const linkFields = { link: null, link_date: null };

//     if (items && items.length > 0) {
//       linkFields.link = items[0].links[0].url;
//       linkFields.link_date = items[0].links[0].modified;
//     }

//     return linkFields;
//   }

//   /** Set flag for if cited record is a government document
//    * @param {array} measurements Measurement objects attached to the work record
//    *
//    * @returns {boolean} Flag designating government report status
//    */
//   static isGovernmentReport(measurements: any) {
//     let govReport = measurements
//       ? measurements.filter((m: any) => m.quantity === "government_document")[0]
//       : { value: 0 };
//     if (!govReport) {
//       govReport = { value: 0 };
//     }

//     return !!govReport.value;
//   }
// }
