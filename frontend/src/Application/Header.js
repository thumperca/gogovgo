/**
 * Created by vathavaria on 6/23/17.
 */

import React, { Component } from "react";
import HowItWorks from "./HowItWorks";
import { Nav, Navbar, NavItem } from "react-bootstrap";
import { withRouter } from "react-router-dom";

class Header extends Component {
    constructor(props, context) {
        super(props, context);
        this.state = {
            howItWorksShow: false,
            user: null,
            dropdown: false
        };
    }

    componentDidMount() {
        this.setUser();
        window.addEventListener("storage", this.setUser.bind(this));
    }

    componentWillUnmount() {
        window.removeEventListener("storage", this.setUser.bind(this));
    }

    setUser() {
        let user = localStorage.getItem("user");
        if (user) user = JSON.parse(user);
        this.setState({ user: user });
    }

    render() {
        let howItWorksClose = () => this.setState({ howItWorksShow: false });
        const goto = url => this.props.history.push(url);

        const { user } = this.state;

        const userIcon = {
            marginRight: "5px",
            fontSize: "17px"
        };

        let navItem = (
            <Nav pullRight>
                <NavItem className="nav-link how-it-work" onClick={() => goto("/signup")}>
                    <i className="fa fa-user-circle" style={userIcon} />
                    Sign up
                </NavItem>
            </Nav>
        );
        if (user) {
            navItem = (
                <Nav pullRight>
                    <NavItem
                        className="nav-link how-it-work user"
                        onClick={() => this.setState({ dropdown: !this.state.dropdown })}
                    >
                        <span>{user.firstName}</span>
                        <i className="fa fa-angle-down" />
                        <i className="fa fa-user-circle" />
                        <div className="profile-option-mobile">
                            <span>Edit Profile</span>
                            <span>Logout</span>
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
