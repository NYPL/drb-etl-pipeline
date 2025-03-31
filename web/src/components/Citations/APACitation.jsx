// import React from "react";

// type OwnProps = {
//   title?: string;
//   subTitle?: string;
//   agents?: {
//     authors?: string[];
//     editors?: string[];
//     translators?: string[];
//     illustrators?: string[];
//     publishers?: string[];
//     contributors?: string[];
//   };
//   publicationYear?: string;
//   edition?: string;
//   volume?: string;
//   sourceLink?: string;
//   isGovernmentDoc?: boolean;
// };

// type Props = OwnProps & typeof APACitation.defaultProps;

// // This provides an APA citation as a formatted component for a specific edition of a work.
// class APACitation extends React.Component<Props> {
//   static defaultProps = {
//     title: "",
//     subTitle: "",
//     agents: {
//       authors: [],
//       editors: [],
//       translators: [],
//       contributors: [],
//       publishers: [],
//       illustrators: [],
//     },
//     publicationYear: null,
//     edition: "",
//     volume: "",
//     sourceLink: "",
//     isGovernmentDoc: false,
//   };

//   authors: any;
//   edition: any;
//   editors: any;
//   govReportStatus: any;
//   illustators: any;
//   illustrators: any;
//   link: any;
//   pubYear: any;
//   publishers: any;
//   title: any;
//   translators: any;
//   volume: any;

//   /** Transforms first names into capitalized initials
//    * @param {string} name First name(s) of an agent to be transformed
//    *
//    * @returns {string} Initials for the supplied names
//    */
//   static getInitials(name: any) {
//     return name
//       .trim()
//       .split(/\s+/)
//       .map((i: any) => `${i.substr(0, 1).toUpperCase()}.`)
//       .join(" ");
//   }

//   // Invokes methods to format data received from props
//   componentWillMount() {
//     this.formatCitationData();
//   }

//   // Set formatted string components to be combined into the full APA citation element
//   formatCitationData() {
//     // @ts-expect-error ts-migrate(2339) FIXME: Property 'subTitle' does not exist on type 'never'... Remove this comment to see the full error message
//     this.title = this.props.subTitle
//       ? // @ts-expect-error ts-migrate(2339) FIXME: Property 'title' does not exist on type 'never'.
//         `${this.props.title}: ${this.props.subTitle}`
//       : // @ts-expect-error ts-migrate(2339) FIXME: Property 'title' does not exist on type 'never'.
//         this.props.title;

//     this.authors = this.formatAgentNames("authors");
//     const rawEditors = this.formatAgentNames(
//       "editors",
//       // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//       this.props.agents.authors.length > 0
//     );
//     this.editors = `${rawEditors}, (Ed${
//       // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//       this.props.agents.editors.length === 1 ? "." : "s."
//     })`;
//     this.translators = `${this.formatAgentNames("translators", true)}, Trans.`;
//     this.illustrators = `${this.formatAgentNames(
//       "illustrators",
//       true
//     )}, Illus.`;

//     // @ts-expect-error ts-migrate(2339) FIXME: Property 'publicationYear' does not exist on type ... Remove this comment to see the full error message
//     this.pubYear = this.props.publicationYear
//       ? // @ts-expect-error ts-migrate(2339) FIXME: Property 'publicationYear' does not exist on type ... Remove this comment to see the full error message
//         ` (${this.props.publicationYear})`
//       : "";
//     // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//     this.publishers = this.props.agents.publishers.join(", ");

//     // @ts-expect-error ts-migrate(2339) FIXME: Property 'edition' does not exist on type 'never'.
//     this.edition = this.props.edition ? ` (${this.props.edition})` : "";
//     // @ts-expect-error ts-migrate(2339) FIXME: Property 'volume' does not exist on type 'never'.
//     this.volume = this.props.volume ? ` (${this.props.volume})` : "";

//     // @ts-expect-error ts-migrate(2339) FIXME: Property 'sourceLink' does not exist on type 'neve... Remove this comment to see the full error message
//     this.link = this.props.sourceLink ? (
//       // @ts-expect-error ts-migrate(2339) FIXME: Property 'sourceLink' does not exist on type 'neve... Remove this comment to see the full error message
//       <a href={`https://${this.props.sourceLink}`}>{this.props.sourceLink}</a>
//     ) : (
//       ""
//     );

//     // @ts-expect-error ts-migrate(2339) FIXME: Property 'isGovernmentDoc' does not exist on type ... Remove this comment to see the full error message
//     this.govReportStatus = this.props.isGovernmentDoc;
//   }

//   /** Transform array of agents into a comma-delimited string
//    * @param {string} agentType Agent role (e.g. author) to format for display
//    * @param {boolean} nameFirst Sets to display names as Last, Initials or Initials Last. Defaults to false
//    *
//    * @returns {string} Comma delimited string of transformed agent names
//    */
//   formatAgentNames(agentType: any, nameFirst = false) {
//     // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//     return this.props.agents[agentType]
//       .map((a: any) => {
//         let firstNames;
//         let lastName;
//         const cleanName = a.replace(/\(.+\)/, "");
//         if (a.indexOf(",") > -1) {
//           [lastName, firstNames] = cleanName.split(",");
//         } else {
//           firstNames = cleanName.split(/\s+/);
//           lastName = firstNames.pop();
//           firstNames = firstNames.join(" ");
//         }
//         firstNames = firstNames || "";
//         if (nameFirst) {
//           return `${APACitation.getInitials(firstNames)} ${lastName}`;
//         }

//         return `${lastName}, ${APACitation.getInitials(firstNames)}`;
//       })
//       .join(", ");
//   }

//   /**
//    * Return a government report citation when govReportStatus is true
//    * Citations for these documents are somewhat simpler than for monographs
//    *
//    * Standard format
//    * Authors OR Editors (Ed.) (Publication Year) <em>Title: Subtitle</em> Publishers. Link
//    *
//    * @returns {object} Element to be displayed
//    */
//   returnGovernmentReport() {
//     let responsibilityStatement = "";
//     // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//     if (this.props.agents.authors.length > 0) {
//       responsibilityStatement = this.authors;
//       // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//     } else if (this.props.agents.editors.length > 0) {
//       responsibilityStatement = this.editors;
//     }

//     return (
//       <>
//         {`${responsibilityStatement}${this.pubYear}. `}

//         <em>{`${this.title} `}</em>
//         {`${this.publishers}. `}
//         {this.link}
//       </>
//     );
//   }

//   /**
//    * Returns a formatted citation for a monograph, including the volume if present
//    * Monograph citations can include all metadata passed into this component. Importantly
//    * the editors block can change position depending on the presence of authors
//    *
//    * Authors Format
//    * Authors (Publication Year) <em>Title: SubTitle</em> (Volume) (Illustrators OR Translators) (Edition) (Editors) Publishers. Link
//    * No Authors Format
//    * Editors (Ed.) (Publication Year) <em>Title: SubTitle</em> (Volume) (Illustrators OR Translators) (Edition) Publishers. Link
//    *
//    * @param {boolean} addVolume Set if volume data is present to return in citation
//    *
//    * @returns {object} Formatted element to be displayed
//    */
//   returnMonographCitation(addVolume = false) {
//     let responsibilityStatement = "";
//     // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//     if (this.props.agents.authors.length > 0) {
//       responsibilityStatement = this.authors;
//       // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//       if (this.props.agents.editors.length > 0) {
//         this.edition = `${this.edition} (${this.editors}).`;
//       }
//       // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//     } else if (this.props.agents.editors.length > 0) {
//       responsibilityStatement = this.editors;
//     }

//     if (
//       // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//       this.props.agents.illustrators.length > 0 &&
//       // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//       this.props.agents.translators.length > 0
//     ) {
//       this.title = `${this.title} (${this.illustrators}, ${this.translators})`;
//       // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//     } else if (this.props.agents.illustrators.length > 0) {
//       this.title = `${this.title} (${this.illustators})`;
//       // @ts-expect-error ts-migrate(2339) FIXME: Property 'agents' does not exist on type 'never'.
//     } else if (this.props.agents.translators.length > 0) {
//       this.title = `${this.title} (${this.translators})`;
//     }

//     return (
//       <>
//         {`${responsibilityStatement}${this.pubYear}. `}

//         <em>{`${this.title}`}</em>
//         {`${addVolume ? this.volume : ""}`}
//         {`${this.edition} `}
//         {`${this.publishers}. `}
//         {this.link}
//       </>
//     );
//   }

//   // Returns appropriate APA citation version
//   render() {
//     const volumeData = this.volume !== "";
//     return (
//       <div className="apa-citation">
//         <strong>APA</strong>

//         <br />
//         {this.govReportStatus && this.returnGovernmentReport()}
//         {!this.govReportStatus && this.returnMonographCitation(volumeData)}
//       </div>
//     );
//   }
// }

// export default APACitation;
