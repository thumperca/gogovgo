/**
 * Created by vathavaria on 6/23/17.
 */

import React, { Component } from "react";
import HowItWorks from "./HowItWorks";
import { Nav, Navbar, NavItem } from "react-bootstrap";
import { withRouter, Link } from "react-router-dom";

class Header extends Component {
    constructor(props, context) {
        super(props, context);
        this.state = { howItWorksShow: false, login: true, dropdown: true };
    }

    signup() {
        this.props.history.push("/signup");
    }

    render() {
        let howItWorksClose = () => this.setState({ howItWorksShow: false });

        const userIcon = {
            marginRight: "5px",
            fontSize: "17px"
        };

        let navItem = (
            <Nav pullRight>
                <NavItem className="nav-link how-it-work" onClick={() => this.signup()}>
                    <i className="fa fa-user-circle" style={userIcon} />
                    Sign up
                </NavItem>
            </Nav>
        );
        if (this.state.login) {
            navItem = (
                <Nav pullRight>
                    <NavItem
                        className="nav-link how-it-work user"
                        onClick={() => this.setState({ dropdown: !this.state.dropdown })}
                    >
                        <span>Manvir</span>
                        <i className="fa fa-angle-down" />
                        <i className="fa fa-user-circle" />
                        <div className="profile-option-mobile">
                            <a>Edit Profile</a>
                            <a>Logout</a>
                        </div>
                    </NavItem>
                </Nav>
            );
        }

        return (
            <Navbar className="main-menu" collapseOnSelect fluid>
                <Navbar.Header>
                    <Navbar.Brand>
                        <a className="main" href="/">
                            <div className="logo">
                                <span className="main">DonaldTrumpReviews.com</span>
                                {/* <span className="slogan">Government, simplified</span> */}
                            </div>
                        </a>
                    </Navbar.Brand>
                    <Navbar.Toggle />
                </Navbar.Header>
                <Navbar.Collapse>
                    {this.state.dropdown && (
                        <div className="profile-option">
                            <a>Edit Profile</a>
                            <a>Logout</a>
                        </div>
                    )}
                    {navItem}
                    <Nav pullRight>
                        <NavItem
                            className="nav-link how-it-work"
                            onClick={() => this.setState({ howItWorksShow: true })}
                        >
                            How it Works
                        </NavItem>
                    </Nav>
                </Navbar.Collapse>
                <HowItWorks show={this.state.howItWorksShow} onHide={howItWorksClose} />
            </Navbar>
        );
    }
}

export default withRouter(Header);
