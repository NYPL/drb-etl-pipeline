import React from "react";
import BaseLink from "next/link";
import {
  Link as DSLink,
  LinkTypes,
} from "@nypl/design-system-react-components";

// allow this component to accept all properties of "a" tag
interface IProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  to: any;
  modifiers?: string[];
  linkType?: LinkTypes;
  isUnderlined?: boolean;
}

const Link = ({
  children,
  to,
  linkType,
  isUnderlined,
  "aria-label": ariaLabel,
  onClick,
}: IProps) => {
  return (
    <DSLink
      href={to}
      as={BaseLink}
      isUnderlined={isUnderlined}
      type={linkType}
      onClick={onClick}
      aria-label={ariaLabel}
      __css={{ width: "100%" }}
    >
      {children}
    </DSLink>
  );
};

Link.displayName = "Link";

export default Link;
